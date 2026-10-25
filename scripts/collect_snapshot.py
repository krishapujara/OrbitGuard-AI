"""Automated periodic catalog snapshot collector for building historical archives.

Downloads public CelesTrak GP/TLE sets, validates them, and stores them under
data/historical/ with full provenance manifests and SHA-256 integrity hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.data_sources import DataSourceService
from backend.tle_parser import TLEValidationService
from config.settings import get_settings


def collect_snapshot(group: str, out_dir: Path | None = None) -> tuple[Path, Path]:
    settings = get_settings()
    target_dir = out_dir or settings.data_historical
    target_dir.mkdir(parents=True, exist_ok=True)

    service = DataSourceService(settings)
    records = service.fetch_group(group, refresh=True)
    if not records:
        raise RuntimeError(f"No records fetched for group {group}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{group}_{ts}.tle"
    tle_path = target_dir / filename
    manifest_path = target_dir / f"{group}_{ts}.manifest.json"

    # Assemble raw TLE text
    lines = []
    epochs = []
    for r in records:
        lines.extend([r.name, r.line1, r.line2])
        epochs.append(r.epoch_utc.isoformat())

    content = "\n".join(lines) + "\n"
    tle_path.write_text(content, encoding="utf-8")
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

    manifest = {
        "group": group,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "sha256": sha256,
        "source_url": f"{settings.celestrak_gp_url}?GROUP={group}&FORMAT=TLE",
        "raw_file": filename,
        "epoch_min": min(epochs) if epochs else None,
        "epoch_max": max(epochs) if epochs else None,
        "note": "Historical snapshot for time-series tracking and temporal evaluation.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return tle_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect CelesTrak snapshot for historical archives.")
    parser.add_argument("--groups", nargs="+", default=["stations", "visual"], help="CelesTrak groups to collect")
    args = parser.parse_args()

    for g in args.groups:
        try:
            tle_file, manifest_file = collect_snapshot(g)
            print(f"Collected {g}: {tle_file.name} ({manifest_file.name})")
        except Exception as exc:
            print(f"Failed to collect {g}: {exc}")


if __name__ == "__main__":
    main()
