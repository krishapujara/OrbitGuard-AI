"""CelesTrak GP client with retries, caching, and provenance.

Documented query interface (Kelso, CelesTrak GP data formats):
https://celestrak.org/NORAD/elements/gp.php?{QUERY}=VALUE[&FORMAT=VALUE]
FORMAT=TLE is requested so records can be checksum-validated as two-line sets.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from backend.exceptions import (
    CatalogEmptyError,
    DataSourceError,
    ObjectNotFoundError,
    RateLimitedError,
)
from backend.logging_utils import log_event
from backend.models import OrbitalRecord
from backend.tle_parser import TLEValidationService
from config.settings import Settings, get_settings

TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
PERMANENT_STATUS = {400, 401, 403, 404, 405, 410}


class DataSourceService:
    def __init__(
        self,
        settings: Settings | None = None,
        session: requests.Session | None = None,
        validator: TLEValidationService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.session = session or requests.Session()
        self.validator = validator or TLEValidationService()

    def search_by_name(self, name: str, *, refresh: bool = False) -> list[OrbitalRecord]:
        return self._query({"NAME": name.strip(), "FORMAT": "TLE"}, refresh=refresh)

    def search_by_catalog_id(self, catalog_id: str, *, refresh: bool = False) -> list[OrbitalRecord]:
        catalog_id = catalog_id.strip()
        records = self._query({"CATNR": catalog_id, "FORMAT": "TLE"}, refresh=refresh)
        if not records:
            raise ObjectNotFoundError(
                f"No GP record was returned for catalog identifier {catalog_id}. "
                "The object may be absent from the public CelesTrak GP set."
            )
        return records

    def fetch_group(self, group: str, *, refresh: bool = False) -> list[OrbitalRecord]:
        group = group.strip().lower()
        records = self._query({"GROUP": group, "FORMAT": "TLE"}, refresh=refresh)
        if not records:
            raise CatalogEmptyError(f"CelesTrak returned no TLE records for GROUP={group}.")
        return records

    def parse_upload(self, text: str, filename: str) -> tuple[list[OrbitalRecord], list[dict[str, str]]]:
        if not text.strip():
            raise DataSourceError("Uploaded file is empty.")
        return self.validator.parse_text(
            text,
            source=f"upload:{filename}",
            retrieved_at=datetime.now(timezone.utc),
            source_url=None,
            from_cache=False,
        )

    def _query(self, params: dict[str, str], *, refresh: bool) -> list[OrbitalRecord]:
        url = f"{self.settings.celestrak_gp_url}?{urlencode(params)}"
        cached = None if refresh else self._read_cache(url)
        if cached is not None:
            text, retrieved_at = cached
            records, _issues = self.validator.parse_text(
                text,
                source="CelesTrak GP",
                retrieved_at=retrieved_at,
                source_url=url,
                from_cache=True,
            )
            for rec in records:
                rec.cache_retrieved_at = retrieved_at
            log_event("info", "catalog_cache_hit", url=url, n=len(records))
            return records
        text = self._http_get(url)
        retrieved_at = datetime.now(timezone.utc)
        self._write_cache(url, text, retrieved_at, params)
        records, issues = self.validator.parse_text(
            text,
            source="CelesTrak GP",
            retrieved_at=retrieved_at,
            source_url=url,
            from_cache=False,
        )
        log_event("info", "catalog_fetched", url=url, n=len(records), issues=len(issues))
        return records

    def _http_get(self, url: str) -> str:
        delay = self.settings.retry_backoff_seconds
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.settings.request_timeout_seconds)
            except requests.Timeout as exc:
                last_error = exc
                log_event("warning", "celestrak_timeout", url=url, attempt=attempt)
                if attempt >= self.settings.max_retries:
                    raise DataSourceError(
                        "CelesTrak request timed out. Check network connectivity and retry."
                    ) from exc
                time.sleep(delay)
                delay *= 2
                continue
            except requests.ConnectionError as exc:
                last_error = exc
                log_event("warning", "celestrak_connection_error", url=url, attempt=attempt)
                if attempt >= self.settings.max_retries:
                    raise DataSourceError(
                        "Could not connect to CelesTrak. Check internet access and try again. "
                        "Previously cached catalogs remain usable if shown as cached."
                    ) from exc
                time.sleep(delay)
                delay *= 2
                continue
            status = response.status_code
            if status in PERMANENT_STATUS:
                raise DataSourceError(f"CelesTrak returned HTTP {status} for {url}.")
            if status == 429:
                if attempt >= self.settings.max_retries:
                    raise RateLimitedError(
                        "CelesTrak rate-limited the request. Wait before refreshing catalogs."
                    )
                retry_after = response.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
                time.sleep(wait)
                delay *= 2
                continue
            if status in TRANSIENT_STATUS:
                last_error = DataSourceError(f"HTTP {status}")
                if attempt >= self.settings.max_retries:
                    raise DataSourceError(f"CelesTrak returned HTTP {status} after retries.")
                time.sleep(delay)
                delay *= 2
                continue
            if status != 200:
                raise DataSourceError(f"CelesTrak returned HTTP {status}.")
            text = response.text or ""
            if not text.strip():
                raise CatalogEmptyError("CelesTrak returned an empty body.")
            if "No GP data found" in text or text.strip().lower().startswith("<!doctype"):
                return ""
            return text
        raise DataSourceError(f"CelesTrak request failed: {last_error}")

    def cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return self.settings.data_cache / f"{digest}.tle"

    def _read_cache(self, url: str) -> Optional[tuple[str, datetime]]:
        path = self.cache_path(url)
        meta_path = path.with_suffix(".json")
        if not path.exists() or not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            retrieved_at = datetime.fromisoformat(meta["retrieved_at"])
            age = (datetime.now(timezone.utc) - retrieved_at).total_seconds()
            if age > self.settings.cache_ttl_seconds:
                return None
            text = path.read_text(encoding="utf-8")
            return text, retrieved_at
        except (OSError, ValueError, KeyError):
            return None

    def _write_cache(self, url: str, text: str, retrieved_at: datetime, params: dict[str, str]) -> None:
        path = self.cache_path(url)
        meta = {
            "url": url,
            "retrieved_at": retrieved_at.isoformat(),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "params": params,
            "ttl_seconds": self.settings.cache_ttl_seconds,
        }
        path.write_text(text, encoding="utf-8")
        path.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        group = params.get("GROUP") or params.get("CATNR") or params.get("NAME") or "query"
        raw_path = self.settings.data_raw / f"{group}_{retrieved_at.strftime('%Y%m%dT%H%M%SZ')}.tle"
        try:
            raw_path.write_text(text, encoding="utf-8")
            manifest = {
                **meta,
                "raw_path": raw_path.name,
                "n_bytes": len(text.encode("utf-8")),
            }
            manifest_path = self.settings.data_manifests / f"{raw_path.stem}.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        except OSError as exc:
            log_event("warning", "raw_save_failed", error=str(exc))

    def cache_status(self) -> list[dict[str, Any]]:
        items = []
        for meta_path in sorted(self.settings.data_cache.glob("*.json")):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                retrieved = datetime.fromisoformat(meta["retrieved_at"])
                age = (datetime.now(timezone.utc) - retrieved).total_seconds()
                items.append(
                    {
                        "url": meta.get("url"),
                        "retrieved_at": meta.get("retrieved_at"),
                        "age_seconds": age,
                        "fresh": age <= self.settings.cache_ttl_seconds,
                        "sha256": meta.get("sha256"),
                    }
                )
            except (OSError, ValueError, KeyError):
                continue
        return items


def freshness_warnings(record: OrbitalRecord, horizon_hours: float) -> list[str]:
    """Stale-data policy: warn from both element age and forecast horizon.

    Public TLEs are fitted mean elements. Propagation error typically grows with
    both element age and how far the forecast extends beyond epoch. There is no
    single certified age cutoff. This policy warns when age exceeds 48 hours or
    half the requested horizon, whichever comparison the user should see.
    """
    age = record.element_age_hours()
    warnings = []
    if age > 48:
        warnings.append(
            f"Orbital elements for {record.name} ({record.catalog_id}) are {age:.1f} h old. "
            "SGP4 error can grow to kilometres per day; treat long-range geometry as approximate."
        )
    if horizon_hours > 0 and age > 0.5 * horizon_hours:
        warnings.append(
            f"Element age ({age:.1f} h) is large relative to the {horizon_hours:.0f} h forecast horizon."
        )
    return warnings
