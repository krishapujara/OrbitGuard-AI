"""Download a CelesTrak GP group and store it under data/raw with a manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.data_sources import DataSourceService
from config.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="stations", help="CelesTrak GROUP name")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    service = DataSourceService(settings)
    records = service.fetch_group(args.group, refresh=args.refresh)
    print(f"Retrieved {len(records)} records for GROUP={args.group}.")
    print(f"Cache directory: {settings.data_cache}")
    print(f"Raw directory: {settings.data_raw}")


if __name__ == "__main__":
    main()
