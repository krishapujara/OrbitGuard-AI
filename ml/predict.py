"""CLI helper to score a feature CSV with the trusted local artifact."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from backend.prediction_service import ModelPredictionService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features_csv", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    frame = pd.read_csv(args.features_csv)
    scored = ModelPredictionService().predict_rows(frame)
    out = args.out or args.features_csv.with_name(args.features_csv.stem + "_scored.csv")
    scored.to_csv(out, index=False)
    print(f"Wrote {out}")
    print("ml_proxy_score is a proxy-task score, not a collision probability.")


if __name__ == "__main__":
    main()
