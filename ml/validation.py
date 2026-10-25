"""Leakage-resistant splitting for orbital pair records."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def chronological_group_split(
    frame: pd.DataFrame,
    *,
    time_col: str = "target_epoch_utc",
    group_col: str = "candidate_id",
    train_frac: float = 0.6,
    val_frac: float = 0.2,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Split by group membership after sorting groups by earliest epoch.

    Random row splits are not used as the evaluation protocol. Groups (candidate
    catalog IDs) are ordered by their earliest target epoch so later epochs are
    preferentially assigned to validation/test when timestamps differ. If all
    epochs are identical (single catalog snapshot), groups are still held out
    intact; that limitation is recorded in the returned metadata.
    """
    if frame.empty:
        raise ValueError("Cannot split an empty frame.")
    df = frame.copy()
    df["_epoch"] = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    group_times = df.groupby(group_col)["_epoch"].min().sort_values()
    unique_times = group_times.dropna().nunique()
    groups = list(group_times.index)
    n = len(groups)
    if n < 6:
        raise ValueError(
            f"Need at least 6 distinct {group_col} groups for a grouped split; found {n}."
        )
    n_train = max(1, int(n * train_frac))
    n_val = max(1, int(n * val_frac))
    if n_train + n_val >= n:
        n_val = max(1, n - n_train - 1)
    train_groups = set(groups[:n_train])
    val_groups = set(groups[n_train : n_train + n_val])
    test_groups = set(groups[n_train + n_val :])
    train = df[df[group_col].isin(train_groups)].drop(columns=["_epoch"])
    val = df[df[group_col].isin(val_groups)].drop(columns=["_epoch"])
    test = df[df[group_col].isin(test_groups)].drop(columns=["_epoch"])
    meta = {
        "protocol": "grouped_chronological_holdout",
        "group_col": group_col,
        "time_col": time_col,
        "n_groups": n,
        "unique_group_epochs": int(unique_times),
        "train_groups": n_train,
        "val_groups": len(val_groups),
        "test_groups": len(test_groups),
        "seed": seed,
        "single_snapshot_limitation": unique_times <= 1,
        "note": (
            "If unique_group_epochs is 1, timestamps do not provide a true future test "
            "window; grouping still prevents the same candidate from appearing in multiple splits."
        ),
    }
    return train, val, test, meta


def assert_no_group_leakage(train: pd.DataFrame, other: pd.DataFrame, group_col: str) -> None:
    overlap = set(train[group_col]).intersection(set(other[group_col]))
    if overlap:
        raise AssertionError(f"Group leakage detected for {group_col}: {sorted(overlap)[:5]}")


def grouped_shuffle_preview(frame: pd.DataFrame, group_col: str = "candidate_id", seed: int = 42) -> None:
    """Sanity helper; not used as the primary evaluation split."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    next(splitter.split(frame, groups=frame[group_col]))
