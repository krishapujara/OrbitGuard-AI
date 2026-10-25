"""Application configuration. Paths are relative to the project root."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    app_name: str = "OrbitalGuard AI"
    app_version: str = "0.1.0"
    project_root: Path = PROJECT_ROOT
    celestrak_gp_url: str = field(
        default_factory=lambda: os.getenv(
            "CELESTRAK_BASE_URL",
            "https://celestrak.org/NORAD/elements/gp.php",
        )
    )
    request_timeout_seconds: int = field(
        default_factory=lambda: _int("REQUEST_TIMEOUT_SECONDS", 30)
    )
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5
    cache_ttl_seconds: int = field(
        default_factory=lambda: _int("CACHE_TTL_SECONDS", 6 * 3600)
    )
    max_upload_bytes: int = 2 * 1024 * 1024
    max_candidates: int = 400
    max_plot_points: int = 240
    default_horizon_hours: int = 24
    allowed_horizons_hours: tuple[int, ...] = (6, 12, 24, 48, 72)
    min_sample_seconds: int = 30
    max_sample_seconds: int = 600
    default_sample_seconds: int = 60
    default_threshold_km: float = 25.0
    coarse_margin: float = 4.0
    earth_radius_km: float = 6378.137  # WGS-84 equatorial radius (spherical alt. approx.)
    mean_earth_radius_km: float = 6371.0
    logs_dir: Path = PROJECT_ROOT / "logs"
    data_raw: Path = PROJECT_ROOT / "data" / "raw"
    data_processed: Path = PROJECT_ROOT / "data" / "processed"
    data_historical: Path = PROJECT_ROOT / "data" / "historical"
    data_manifests: Path = PROJECT_ROOT / "data" / "manifests"
    data_cache: Path = PROJECT_ROOT / "data" / "cache"
    ml_artifacts: Path = PROJECT_ROOT / "ml" / "artifacts"
    catalog_groups: tuple[str, ...] = (
        "stations",
        "visual",
        "active",
        "weather",
        "science",
        "cubesat",
        "starlink",
        "oneweb",
        "gps-ops",
        "geo",
        "engineer",
        "education",
        "military",
        "radar",
        "debris",
        "iridium-33-debris",
        "cosmos-2251-debris",
        "fengyun-1c-debris",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    for path in (
        settings.logs_dir,
        settings.data_raw,
        settings.data_processed,
        settings.data_historical,
        settings.data_manifests,
        settings.data_cache,
        settings.ml_artifacts,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return settings
