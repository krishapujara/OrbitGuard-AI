from __future__ import annotations

import pandas as pd
import pytest

from ml.validation import assert_no_group_leakage, chronological_group_split


def test_grouped_split_holds_out_candidates() -> None:
    rows = []
    for i in range(12):
        rows.append(
            {
                "candidate_id": f"c{i}",
                "target_epoch_utc": f"2019-12-0{(i % 9) + 1}T00:00:00+00:00",
                "x": i,
            }
        )
    frame = pd.DataFrame(rows)
    train, val, test, meta = chronological_group_split(frame, seed=0)
    assert_no_group_leakage(train, val, "candidate_id")
    assert_no_group_leakage(train, test, "candidate_id")
    assert_no_group_leakage(val, test, "candidate_id")
    assert meta["protocol"] == "grouped_chronological_holdout"
    assert len(train) + len(val) + len(test) == len(frame)


def test_split_rejects_too_few_groups() -> None:
    frame = pd.DataFrame(
        {
            "candidate_id": ["a", "b"],
            "target_epoch_utc": ["2019-01-01T00:00:00+00:00"] * 2,
        }
    )
    with pytest.raises(ValueError, match="at least 6"):
        chronological_group_split(frame)
