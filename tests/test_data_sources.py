from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

from backend.data_sources import DataSourceService, freshness_warnings
from backend.exceptions import DataSourceError, ObjectNotFoundError, RateLimitedError
from tests.conftest import SAMPLE_TLE


class FakeResponse:
    def __init__(self, status_code: int, text: str = "", headers=None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class FakeSession:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.urls: list[str] = []
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: Any = 0):
        self.urls.append(url)
        if not self.responses:
            raise AssertionError("unexpected HTTP call")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_fetch_group_parses_and_caches(tmp_path, monkeypatch) -> None:
    from config.settings import Settings

    settings = Settings(
        data_cache=tmp_path / "cache",
        data_raw=tmp_path / "raw",
        data_manifests=tmp_path / "manifests",
        data_processed=tmp_path / "processed",
        data_historical=tmp_path / "hist",
        logs_dir=tmp_path / "logs",
        ml_artifacts=tmp_path / "ml",
        cache_ttl_seconds=10_000,
    )
    for path in (
        settings.data_cache,
        settings.data_raw,
        settings.data_manifests,
        settings.data_processed,
        settings.data_historical,
        settings.logs_dir,
        settings.ml_artifacts,
    ):
        path.mkdir(parents=True, exist_ok=True)
    text = SAMPLE_TLE.read_text(encoding="utf-8")
    session = FakeSession([FakeResponse(200, text)])
    service = DataSourceService(settings=settings, session=session)
    records = service.fetch_group("stations", refresh=True)
    assert len(records) == 4
    assert records[0].source_url and "GROUP=stations" in records[0].source_url
    assert not records[0].from_cache
    cached = service.fetch_group("stations", refresh=False)
    assert cached[0].from_cache
    assert len(session.urls) == 1


def test_missing_catalog_id(tmp_path) -> None:
    from config.settings import Settings

    settings = Settings(data_cache=tmp_path / "cache", data_raw=tmp_path / "raw", data_manifests=tmp_path / "m")
    settings.data_cache.mkdir(parents=True, exist_ok=True)
    settings.data_raw.mkdir(parents=True, exist_ok=True)
    settings.data_manifests.mkdir(parents=True, exist_ok=True)
    session = FakeSession([FakeResponse(200, "No GP data found")])
    service = DataSourceService(settings=settings, session=session)
    with pytest.raises(ObjectNotFoundError):
        service.search_by_catalog_id("99999", refresh=True)


def test_rate_limit(tmp_path, monkeypatch) -> None:
    from config.settings import Settings

    monkeypatch.setattr("backend.data_sources.time.sleep", lambda *_args, **_kwargs: None)
    settings = Settings(data_cache=tmp_path / "cache", data_raw=tmp_path / "raw", data_manifests=tmp_path / "m")
    settings.data_cache.mkdir(parents=True, exist_ok=True)
    settings.data_raw.mkdir(parents=True, exist_ok=True)
    settings.data_manifests.mkdir(parents=True, exist_ok=True)
    session = FakeSession([FakeResponse(429)] * 8)
    service = DataSourceService(settings=settings, session=session)
    with pytest.raises((RateLimitedError, DataSourceError)):
        service.fetch_group("stations", refresh=True)


def test_freshness_warnings_for_old_elements(iss) -> None:
    notes = freshness_warnings(iss, horizon_hours=6)
    assert notes
    assert any("old" in n.lower() or "age" in n.lower() for n in notes)


def test_permanent_http_error(tmp_path) -> None:
    from config.settings import Settings

    settings = Settings(data_cache=tmp_path / "cache", data_raw=tmp_path / "raw", data_manifests=tmp_path / "m")
    settings.data_cache.mkdir(parents=True, exist_ok=True)
    settings.data_raw.mkdir(parents=True, exist_ok=True)
    settings.data_manifests.mkdir(parents=True, exist_ok=True)
    session = FakeSession([FakeResponse(404, "nope")])
    service = DataSourceService(settings=settings, session=session)
    with pytest.raises(DataSourceError, match="404"):
        service.fetch_group("stations", refresh=True)


def test_connect_timeout_handling(tmp_path, monkeypatch) -> None:
    from config.settings import Settings

    monkeypatch.setattr("backend.data_sources.time.sleep", lambda *_args, **_kwargs: None)
    settings = Settings(
        data_cache=tmp_path / "cache",
        data_raw=tmp_path / "raw",
        data_manifests=tmp_path / "m",
        max_retries=1,
    )
    settings.data_cache.mkdir(parents=True, exist_ok=True)
    settings.data_raw.mkdir(parents=True, exist_ok=True)
    settings.data_manifests.mkdir(parents=True, exist_ok=True)
    session = FakeSession([requests.exceptions.ConnectTimeout("connection timed out")] * 3)
    service = DataSourceService(settings=settings, session=session)
    with pytest.raises(DataSourceError, match="connection timed out"):
        service.fetch_group("stations", refresh=True)


def test_read_timeout_handling(tmp_path, monkeypatch) -> None:
    from config.settings import Settings

    monkeypatch.setattr("backend.data_sources.time.sleep", lambda *_args, **_kwargs: None)
    settings = Settings(
        data_cache=tmp_path / "cache",
        data_raw=tmp_path / "raw",
        data_manifests=tmp_path / "m",
        max_retries=1,
    )
    settings.data_cache.mkdir(parents=True, exist_ok=True)
    settings.data_raw.mkdir(parents=True, exist_ok=True)
    settings.data_manifests.mkdir(parents=True, exist_ok=True)
    session = FakeSession([requests.exceptions.ReadTimeout("read timed out")] * 3)
    service = DataSourceService(settings=settings, session=session)
    with pytest.raises(DataSourceError, match="read timed out"):
        service.fetch_group("stations", refresh=True)


def test_dns_failure_handling(tmp_path, monkeypatch) -> None:
    from config.settings import Settings

    monkeypatch.setattr("backend.data_sources.time.sleep", lambda *_args, **_kwargs: None)
    settings = Settings(
        data_cache=tmp_path / "cache",
        data_raw=tmp_path / "raw",
        data_manifests=tmp_path / "m",
        max_retries=1,
    )
    settings.data_cache.mkdir(parents=True, exist_ok=True)
    settings.data_raw.mkdir(parents=True, exist_ok=True)
    settings.data_manifests.mkdir(parents=True, exist_ok=True)
    session = FakeSession([requests.exceptions.ConnectionError("getaddrinfo failed: name or service not known")] * 3)
    service = DataSourceService(settings=settings, session=session)
    with pytest.raises(DataSourceError, match="DNS lookup failed"):
        service.fetch_group("stations", refresh=True)


def test_user_agent_header_set() -> None:
    service = DataSourceService()
    ua = service.session.headers.get("User-Agent")
    assert ua is not None
    assert "OrbitalGuardAI" in ua
    assert "celestrak" not in ua.lower() or "orbitguardai" in ua.lower()


def test_find_and_load_offline_snapshot(tmp_path) -> None:
    from config.settings import Settings

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    text = SAMPLE_TLE.read_text(encoding="utf-8")
    meta = {
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=TLE",
        "retrieved_at": "2026-10-14T05:00:00+00:00",
        "sha256": "abc1234",
        "params": {"GROUP": "stations", "FORMAT": "TLE"},
        "ttl_seconds": 21600,
    }
    tle_file = cache_dir / "test_snapshot.tle"
    tle_file.write_text(text, encoding="utf-8")
    json_file = cache_dir / "test_snapshot.json"
    json_file.write_text(json.dumps(meta), encoding="utf-8")

    settings = Settings(
        data_cache=cache_dir,
        data_raw=raw_dir,
        data_manifests=tmp_path / "m",
        project_root=tmp_path,
    )
    service = DataSourceService(settings=settings)
    snap = service.find_offline_snapshot("stations")
    assert snap is not None
    assert snap["source_type"] == "disk_cache"
    assert snap["group"] == "stations"

    records, issues = service.load_offline_snapshot(snap)
    assert len(records) == 4
    assert records[0].from_cache
    assert records[0].cache_retrieved_at is not None
