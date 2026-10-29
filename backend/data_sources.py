"""CelesTrak GP client with retries, caching, provenance, and resilient offline fallbacks.

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
        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            user_agent = getattr(
                self.settings,
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (compatible; OrbitalGuardAI/0.1.0; +https://orbitguardai.streamlit.app/)",
            )
            self.session.headers.update(
                {
                    "User-Agent": user_agent,
                    "Accept": "text/plain, */*",
                    "Accept-Encoding": "gzip, deflate",
                }
            )
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
                source="CelesTrak GP (cache)",
                retrieved_at=retrieved_at,
                source_url=url,
                from_cache=True,
            )
            for rec in records:
                rec.cache_retrieved_at = retrieved_at
            log_event("info", "catalog_cache_hit", url=url, n=len(records))
            return records

        try:
            text = self._http_get(url)
            retrieved_at = datetime.now(timezone.utc)
            self._write_cache(url, text, retrieved_at, params)
            records, issues = self.validator.parse_text(
                text,
                source="CelesTrak GP (live)",
                retrieved_at=retrieved_at,
                source_url=url,
                from_cache=False,
            )
            log_event("info", "catalog_fetched", url=url, n=len(records), issues=len(issues))
            return records
        except DataSourceError as exc:
            group_key = params.get("GROUP") or params.get("CATNR") or params.get("NAME") or ""
            if not refresh and group_key:
                offline_snap = self.find_offline_snapshot(group_key)
                if offline_snap is not None:
                    records, _ = self.load_offline_snapshot(offline_snap)
                    log_event(
                        "info",
                        "catalog_offline_fallback",
                        group=group_key,
                        n=len(records),
                        reason=str(exc),
                    )
                    return records
            raise exc

    def _http_get(self, url: str) -> str:
        delay = self.settings.retry_backoff_seconds
        last_error: Exception | None = None
        connect_to = getattr(self.settings, "connect_timeout_seconds", 15.0)
        read_to = getattr(self.settings, "read_timeout_seconds", 30.0)
        timeout_tuple = (connect_to, read_to)
        max_retries = getattr(self.settings, "max_retries", 2)

        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=timeout_tuple)
            except requests.exceptions.ConnectTimeout as exc:
                last_error = exc
                log_event("warning", "celestrak_connect_timeout", url=url, attempt=attempt)
                if attempt >= max_retries:
                    raise DataSourceError(
                        f"CelesTrak connection timed out ({connect_to:.0f}s). Upstream server may be rate-limiting "
                        "cloud datacenter IP addresses (common on Streamlit Cloud). You can load the bundled sample "
                        "or offline cached catalog to continue uninterrupted."
                    ) from exc
                time.sleep(delay)
                delay *= 2
                continue
            except requests.exceptions.ReadTimeout as exc:
                last_error = exc
                log_event("warning", "celestrak_read_timeout", url=url, attempt=attempt)
                if attempt >= max_retries:
                    raise DataSourceError(
                        f"CelesTrak read timed out ({read_to:.0f}s) while downloading catalog data. "
                        "The upstream server is responding slowly. Please retry or use offline sample data."
                    ) from exc
                time.sleep(delay)
                delay *= 2
                continue
            except requests.exceptions.Timeout as exc:
                last_error = exc
                log_event("warning", "celestrak_timeout", url=url, attempt=attempt)
                if attempt >= max_retries:
                    raise DataSourceError(
                        "CelesTrak request timed out. Check network connectivity or use offline sample data."
                    ) from exc
                time.sleep(delay)
                delay *= 2
                continue
            except requests.exceptions.ConnectionError as exc:
                last_error = exc
                log_event("warning", "celestrak_connection_error", url=url, attempt=attempt)
                err_str = str(exc).lower()
                dns_error = any(
                    kw in err_str
                    for kw in ("getaddrinfo failed", "nameresolutionerror", "name or service not known")
                )
                if attempt >= max_retries:
                    if dns_error:
                        raise DataSourceError(
                            "DNS lookup failed for celestrak.org. Check internet access or use offline sample data."
                        ) from exc
                    raise DataSourceError(
                        "Could not connect to CelesTrak. Connection was refused or dropped. "
                        "Check internet access or use offline sample data."
                    ) from exc
                time.sleep(delay)
                delay *= 2
                continue
            status = response.status_code
            if status in PERMANENT_STATUS:
                raise DataSourceError(f"CelesTrak returned HTTP {status} for {url}.")
            if status == 429:
                if attempt >= max_retries:
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
                if attempt >= max_retries:
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

    def find_offline_snapshot(self, group_or_query: str) -> Optional[dict[str, Any]]:
        """Locate an existing local offline snapshot for this group or query on disk.

        Checks data/cache, verified bundled catalogs, data/raw, data/historical, and sample_catalog.tle.
        """
        group_norm = group_or_query.strip().lower()
        now = datetime.now(timezone.utc)

        # 1. Check verified bundled catalog snapshots in data/sample_metadata/catalogs/
        bundled_catalog = self.settings.project_root / "data" / "sample_metadata" / "catalogs" / f"{group_norm}.tle"
        bundled_meta = bundled_catalog.with_suffix(".json")
        if bundled_catalog.exists() and bundled_catalog.stat().st_size > 0:
            retrieved = now
            sha_val = hashlib.sha256(bundled_catalog.read_bytes()).hexdigest()
            if bundled_meta.exists():
                try:
                    meta = json.loads(bundled_meta.read_text(encoding="utf-8"))
                    retrieved = datetime.fromisoformat(meta["retrieved_at"])
                    sha_val = meta.get("sha256", sha_val)
                except Exception:
                    pass
            age_h = (now - retrieved).total_seconds() / 3600.0
            return {
                "source_type": "bundled_catalog",
                "path": bundled_catalog,
                "retrieved_at": retrieved,
                "age_hours": age_h,
                "group": group_norm,
                "sha256": sha_val,
                "description": f"Verified bundled CelesTrak snapshot for '{group_norm}' ({retrieved.strftime('%Y-%m-%d %H:%M UTC')})",
            }

        # 2. Check data/cache metadata
        for meta_path in sorted(self.settings.data_cache.glob("*.json")):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                params = meta.get("params", {})
                grp = params.get("GROUP", "").lower()
                catnr = params.get("CATNR", "").lower()
                name = params.get("NAME", "").lower()
                if group_norm in (grp, catnr, name):
                    tle_path = meta_path.with_suffix(".tle")
                    if tle_path.exists() and tle_path.stat().st_size > 0:
                        retrieved = datetime.fromisoformat(meta["retrieved_at"])
                        age_h = (now - retrieved).total_seconds() / 3600.0
                        return {
                            "source_type": "disk_cache",
                            "path": tle_path,
                            "retrieved_at": retrieved,
                            "age_hours": age_h,
                            "group": group_norm,
                            "sha256": meta.get("sha256"),
                            "description": f"Cached snapshot from {retrieved.strftime('%Y-%m-%d %H:%M UTC')} ({age_h:.1f}h old)",
                        }
            except (OSError, ValueError, KeyError):
                continue

        # 3. Check data/raw for raw snapshots
        raw_matches = sorted(self.settings.data_raw.glob(f"{group_norm}_*.tle"), reverse=True)
        if raw_matches:
            best_raw = raw_matches[0]
            if best_raw.stat().st_size > 0:
                mtime = datetime.fromtimestamp(best_raw.stat().st_mtime, tz=timezone.utc)
                age_h = (now - mtime).total_seconds() / 3600.0
                return {
                    "source_type": "raw_archive",
                    "path": best_raw,
                    "retrieved_at": mtime,
                    "age_hours": age_h,
                    "group": group_norm,
                    "sha256": hashlib.sha256(best_raw.read_bytes()).hexdigest(),
                    "description": f"Raw catalog snapshot from {mtime.strftime('%Y-%m-%d %H:%M UTC')} ({age_h:.1f}h old)",
                }

        # 4. Check data/historical
        hist_matches = sorted(self.settings.data_historical.glob(f"{group_norm}_*.tle"), reverse=True)
        if hist_matches:
            best_hist = hist_matches[0]
            if best_hist.stat().st_size > 0:
                mtime = datetime.fromtimestamp(best_hist.stat().st_mtime, tz=timezone.utc)
                age_h = (now - mtime).total_seconds() / 3600.0
                return {
                    "source_type": "historical",
                    "path": best_hist,
                    "retrieved_at": mtime,
                    "age_hours": age_h,
                    "group": group_norm,
                    "sha256": hashlib.sha256(best_hist.read_bytes()).hexdigest(),
                    "description": f"Historical snapshot from {mtime.strftime('%Y-%m-%d %H:%M UTC')} ({age_h:.1f}h old)",
                }

        # 5. Check bundled sample catalog as universal fallback
        sample_path = self.settings.project_root / "data" / "sample_metadata" / "sample_catalog.tle"
        if sample_path.exists() and sample_path.stat().st_size > 0:
            mtime = datetime.fromtimestamp(sample_path.stat().st_mtime, tz=timezone.utc)
            return {
                "source_type": "bundled_sample",
                "path": sample_path,
                "retrieved_at": mtime,
                "age_hours": 0.0,
                "group": "bundled-sample",
                "sha256": hashlib.sha256(sample_path.read_bytes()).hexdigest(),
                "description": "Bundled offline sample catalog (historical demonstration elements)",
            }

        return None

    def load_offline_snapshot(self, snapshot_info: dict[str, Any]) -> tuple[list[OrbitalRecord], list[dict[str, str]]]:
        """Load and parse an offline snapshot with complete provenance tracking."""
        path: Path = snapshot_info["path"]
        text = path.read_text(encoding="utf-8")
        retrieved_at = snapshot_info["retrieved_at"]
        source_label = f"offline:{snapshot_info['source_type']}:{path.name}"
        records, issues = self.validator.parse_text(
            text,
            source=source_label,
            retrieved_at=retrieved_at,
            source_url=None,
            from_cache=True,
        )
        for rec in records:
            rec.cache_retrieved_at = retrieved_at
        log_event(
            "info",
            "offline_snapshot_loaded",
            source_type=snapshot_info["source_type"],
            path=str(path),
            records=len(records),
            issues=len(issues),
        )
        return records, issues

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
