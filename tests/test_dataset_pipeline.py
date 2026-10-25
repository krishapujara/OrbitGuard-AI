from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from backend.feature_engineering import FEATURE_COLUMNS
from backend.tle_parser import tle_checksum
from ml.build_dataset import build_dataset, load_snapshot
from tests.conftest import SAMPLE_TLE


def test_load_snapshot_parses_sample_catalog():
    records, issues = load_snapshot(SAMPLE_TLE)
    assert len(records) == 4
    assert issues == []
    ids = {r.catalog_id for r in records}
    assert "25544" in ids


def test_build_dataset_creates_dataset_and_metadata(tmp_path, monkeypatch):
    from config.settings import Settings

    custom_settings = Settings(
        project_root=tmp_path,
        data_processed=tmp_path / "processed",
        ml_artifacts=tmp_path / "artifacts",
    )
    custom_settings.data_processed.mkdir(parents=True, exist_ok=True)
    custom_settings.ml_artifacts.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("ml.build_dataset.get_settings", lambda: custom_settings)

    # Create a test snapshot with 8 records with valid checksums
    content = SAMPLE_TLE.read_text(encoding="utf-8")
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    extra = []
    for i in range(0, len(lines), 3):
        name = lines[i] + " DUPE"
        l1 = lines[i+1]
        l2 = lines[i+2]
        cat = str(int(l1[2:7]) + 10000).zfill(5)
        new_l1_68 = l1[:2] + cat + l1[7:68]
        new_l1 = new_l1_68 + str(tle_checksum(new_l1_68))
        new_l2_68 = l2[:2] + cat + l2[7:68]
        new_l2 = new_l2_68 + str(tle_checksum(new_l2_68))
        extra.extend([name, new_l1, new_l2])

    test_snapshot = tmp_path / "test_catalog.tle"
    test_snapshot.write_text(content + "\n" + "\n".join(extra), encoding="utf-8")

    out_csv = build_dataset(
        test_snapshot,
        target_id="25544",
        horizon_hours=6,
        threshold_km=5000.0,
        sample_seconds=300,
        max_candidates=10,
        max_targets=1,
    )

    assert out_csv.exists()
    df = pd.read_csv(out_csv)
    assert len(df) > 0

    # Ensure all required feature columns are present
    for col in FEATURE_COLUMNS:
        assert col in df.columns, f"Feature column {col} missing from dataset"

    # Ensure proxy target column is present and valid binary
    assert "below_threshold_proxy" in df.columns
    unique_vals = set(df["below_threshold_proxy"].unique())
    assert unique_vals.issubset({0, 1})

    # Verify metadata JSON
    meta_json = out_csv.with_suffix(".meta.json")
    assert meta_json.exists()
    meta = json.loads(meta_json.read_text(encoding="utf-8"))
    assert meta["target_definition"] == "below_threshold_proxy"
    assert "Not a collision outcome" in meta["target_description"]
    assert meta["feature_schema"] == FEATURE_COLUMNS
    assert meta["threshold_km"] == 5000.0
