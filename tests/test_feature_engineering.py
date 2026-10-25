from __future__ import annotations

from datetime import datetime, timezone

from backend.feature_engineering import FEATURE_COLUMNS, FeatureEngineeringService


def test_features_exclude_tca_and_refined_miss(sample_records) -> None:
    target = next(r for r in sample_records if r.catalog_id == "25544")
    cand = next(r for r in sample_records if r.catalog_id == "20580")
    service = FeatureEngineeringService()
    row = service.features_from_records(
        target,
        cand,
        at=datetime(2019, 12, 9, 17, tzinfo=timezone.utc),
        horizon_hours=24,
        sample_seconds=60,
    )
    for col in FEATURE_COLUMNS:
        assert col in row
    leaked = service.leak_check_columns(list(row.keys()))
    assert leaked == []
    assert "min_separation_km" not in row
    assert "tca_utc" not in row
    assert row["epoch_separation_km"] is not None
    assert row["epoch_separation_km"] > 0
