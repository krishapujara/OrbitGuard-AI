"""Build a labelled proxy dataset from screening of a stored catalog snapshot.

Proxy target name: below_threshold_proxy
Definition: 1 if refined SGP4 TEME miss distance over the chosen horizon is
<= the screening threshold, else 0. This is not a collision label.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.conjunction_screening import ConjunctionScreeningService
from backend.feature_engineering import FEATURE_COLUMNS, FeatureEngineeringService
from backend.tle_parser import TLEValidationService
from config.settings import get_settings


def load_snapshot(path: Path):
    text = path.read_text(encoding="utf-8")
    records, issues = TLEValidationService().parse_text(
        text,
        source=f"snapshot:{path.name}",
        retrieved_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
        source_url=None,
        from_cache=False,
    )
    return records, issues


def latest_raw_snapshot() -> Path | None:
    settings = get_settings()
    files = sorted(settings.data_raw.glob("*.tle"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def build_dataset(
    snapshot: Path,
    *,
    target_id: str | None = None,
    horizon_hours: float = 24,
    threshold_km: float = 25.0,
    sample_seconds: float = 120,
    max_candidates: int = 80,
    max_targets: int = 3,
) -> Path:
    settings = get_settings()
    records, issues = load_snapshot(snapshot)
    if len(records) < 8:
        raise RuntimeError(
            f"Snapshot {snapshot} has only {len(records)} valid records; need more objects."
        )
    if target_id:
        targets = [r for r in records if r.catalog_id == str(target_id).lstrip("0") or r.catalog_id == str(target_id)]
        if not targets:
            raise RuntimeError(f"Target {target_id} is not in snapshot {snapshot.name}.")
    else:
        targets = records[:max_targets]
    screening = ConjunctionScreeningService()
    features = FeatureEngineeringService()
    seen_canonical_pairs: set[tuple[str, str]] = set()
    rows = []
    for target in targets:
        run = screening.screen(
            target,
            records,
            horizon_hours=horizon_hours,
            threshold_km=threshold_km,
            sample_seconds=sample_seconds,
            max_candidates=max_candidates,
        )
        by_id = {r.catalog_id: r for r in records}
        for approach in run.approaches:
            cand = by_id.get(approach.candidate_id)
            if cand is None:
                continue
            tid = str(target.catalog_id)
            cid = str(cand.catalog_id)
            pair_key = (min(tid, cid), max(tid, cid))
            if pair_key in seen_canonical_pairs:
                continue
            seen_canonical_pairs.add(pair_key)
            rows.append(
                features.features_from_approach(
                    target, cand, approach, at=run.started_at
                )
            )
    if not rows:
        raise RuntimeError("Screening produced no rows for the dataset.")
    df = features.to_frame(rows)
    out = settings.data_processed / "proxy_dataset.csv"
    df.to_csv(out, index=False)
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot.name,
        "n_rows": int(len(df)),
        "n_parse_issues": len(issues),
        "target_definition": "below_threshold_proxy",
        "target_description": (
            "Binary label: refined SGP4 TEME miss distance <= screening threshold "
            "over the requested horizon. Not a collision outcome."
        ),
        "feature_schema": FEATURE_COLUMNS,
        "horizon_hours": horizon_hours,
        "threshold_km": threshold_km,
        "sample_seconds": sample_seconds,
        "label_source": "SGP4 refined screening of the same snapshot (proxy, not observations of collisions)",
    }
    (settings.data_processed / "proxy_dataset.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build geometric proxy ML dataset from a TLE snapshot.")
    parser.add_argument("--snapshot", type=Path, default=None)
    parser.add_argument("--target-id", default=None)
    parser.add_argument("--horizon-hours", type=float, default=24)
    parser.add_argument("--threshold-km", type=float, default=25)
    parser.add_argument("--sample-seconds", type=float, default=120)
    parser.add_argument("--max-candidates", type=int, default=80)
    args = parser.parse_args()
    snapshot = args.snapshot or latest_raw_snapshot()
    if snapshot is None:
        raise SystemExit(
            "No TLE snapshot found in data/raw. Run python scripts/download_catalog.py first."
        )
    path = build_dataset(
        snapshot,
        target_id=args.target_id,
        horizon_hours=args.horizon_hours,
        threshold_km=args.threshold_km,
        sample_seconds=args.sample_seconds,
        max_candidates=args.max_candidates,
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
