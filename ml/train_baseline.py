"""Train a scikit-learn baseline for below_threshold_proxy.

Physical baseline: epoch-separation < threshold (coarse geometry at t0).
ML models: DummyClassifier (most frequent) and LogisticRegression pipeline.
No neural network is trained: a single catalog snapshot does not provide
genuine historical sequences for an LSTM or GNN.
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.exceptions import InsufficientMLDataError
from backend.feature_engineering import FEATURE_COLUMNS
from config.settings import get_settings
from ml.build_dataset import build_dataset, latest_raw_snapshot
from ml.evaluate_model import classification_report_dict, majority_baseline
from ml.validation import assert_no_group_leakage, chronological_group_split

SEED = 42
TARGET = "below_threshold_proxy"


def _pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=400,
                    class_weight="balanced",
                    random_state=SEED,
                ),
            ),
        ]
    )


def train(dataset_csv: Path) -> Path:
    settings = get_settings()
    df = pd.read_csv(dataset_csv)
    if TARGET not in df.columns:
        raise InsufficientMLDataError("Dataset is missing below_threshold_proxy labels.")
    df = df.dropna(subset=[TARGET])
    if len(df) < 20:
        raise InsufficientMLDataError(
            f"Only {len(df)} labelled rows. Need at least 20 pairs from a catalog snapshot."
        )
    pos = int(df[TARGET].sum())
    if pos == 0 or pos == len(df):
        raise InsufficientMLDataError(
            "The proxy label has a single class in this snapshot, so a classifier cannot be evaluated."
        )
    train_df, val_df, test_df, split_meta = chronological_group_split(df, seed=SEED)
    assert_no_group_leakage(train_df, val_df, "candidate_id")
    assert_no_group_leakage(train_df, test_df, "candidate_id")
    if "canonical_pair_id" in df.columns:
        assert_no_group_leakage(train_df, val_df, "canonical_pair_id")
        assert_no_group_leakage(train_df, test_df, "canonical_pair_id")
        assert_no_group_leakage(val_df, test_df, "canonical_pair_id")
    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET].astype(int)
    X_val, y_val = val_df[FEATURE_COLUMNS], val_df[TARGET].astype(int)
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET].astype(int)

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_train, y_train)
    model = _pipeline()
    model.fit(X_train, y_train)

    def pack(split_name, X, y):
        pred = model.predict(X)
        proba = model.predict_proba(X)[:, 1]
        dummy_pred = dummy.predict(X)
        ds_meta_file = dataset_csv.with_suffix(".meta.json")
        thr_km = 25.0
        if ds_meta_file.exists():
            try:
                thr_km = float(json.loads(ds_meta_file.read_text(encoding="utf-8")).get("threshold_km", 25.0))
            except Exception:
                pass
        physical = (X["epoch_separation_km"].fillna(np.inf) <= thr_km).astype(int)
        return {
            "ml": classification_report_dict(y, pred, proba),
            "dummy_majority": classification_report_dict(y, dummy_pred, None),
            "physical_epoch_threshold": classification_report_dict(y, physical, None),
            "majority_constant": classification_report_dict(y, majority_baseline(y), None),
        }

    metrics = {
        "validation": pack("val", X_val, y_val),
        "test": pack("test", X_test, y_test),
    }
    coef = model.named_steps["clf"].coef_[0]
    importance = sorted(
        [
            {"feature": name, "coefficient": float(val)}
            for name, val in zip(FEATURE_COLUMNS, coef)
        ],
        key=lambda x: abs(x["coefficient"]),
        reverse=True,
    )
    meta = {
        "trusted_origin": "orbitalguard-ai-local",
        "model_type": "LogisticRegression",
        "training_dataset_version": dataset_csv.name,
        "target_definition": TARGET,
        "target_description": (
            "Proxy label: refined SGP4 miss distance <= screening threshold. "
            "Not a real-world collision probability."
        ),
        "feature_schema": FEATURE_COLUMNS,
        "preprocessing": "SimpleImputer(median)+StandardScaler fitted on training groups only",
        "split": split_meta,
        "metrics": metrics,
        "feature_coefficients": importance,
        "random_seed": SEED,
        "library_versions": {
            "python": platform.python_version(),
            "sklearn": __import__("sklearn").__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Labels are generated from SGP4 of the same snapshot, so the model approximates screening, not observed collisions.",
            "A single snapshot cannot support true future-event validation.",
            "Predicted scores are not calibrated collision probabilities.",
        ],
        "ml_improves_physical_baseline": _improves(
            metrics["test"]["ml"], metrics["test"]["physical_epoch_threshold"]
        ),
    }
    model_path = settings.ml_artifacts / "baseline_model.joblib"
    meta_path = settings.ml_artifacts / "baseline_model.meta.json"
    joblib.dump({"pipeline": model, "dummy": dummy}, model_path)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Synchronize to models/artifacts for external compatibility
    alt_dir = settings.project_root / "models" / "artifacts"
    alt_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "dummy": dummy}, alt_dir / "baseline_model.joblib")
    (alt_dir / "baseline_model.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return model_path


def _improves(ml_metrics: dict, baseline: dict) -> dict:
    return {
        "f1_delta": ml_metrics["f1"] - baseline["f1"],
        "claim": (
            "Compare F1/PR-AUC on the grouped test set. Improvement is claimed only when "
            "the ML F1 exceeds the physical epoch-threshold baseline on that held-out set."
        ),
        "ml_f1_gt_physical_f1": ml_metrics["f1"] > baseline["f1"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--build-if-missing", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    dataset = args.dataset or (settings.data_processed / "proxy_dataset.csv")
    if not dataset.exists():
        if not args.build_if_missing:
            raise SystemExit(
                f"{dataset} not found. Run python -m ml.build_dataset or pass --build-if-missing."
            )
        snapshot = latest_raw_snapshot()
        if snapshot is None:
            raise SystemExit("No data/raw snapshot. Run python scripts/download_catalog.py")
        dataset = build_dataset(snapshot)
    path = train(dataset)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
