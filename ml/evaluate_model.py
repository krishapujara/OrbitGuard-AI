"""Compute honest classification metrics for the proxy task."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
    roc_auc_score,
    average_precision_score,
)


def classification_report_dict(y_true, y_pred, y_score=None) -> dict[str, Any]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    prevalence = float(y_true.mean()) if len(y_true) else float("nan")
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    out: dict[str, Any] = {
        "n": int(len(y_true)),
        "prevalence_positive": prevalence,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix_labels": [0, 1],
        "confusion_matrix": cm,
        "accuracy_note": (
            "Accuracy is misleading for rare-event labels; prefer precision, recall, "
            "F1, and PR-AUC when prevalence is low."
        ),
    }
    if y_score is not None and len(np.unique(y_true)) == 2:
        y_score = np.asarray(y_score, dtype=float)
        out["roc_auc"] = float(roc_auc_score(y_true, y_score))
        out["pr_auc"] = float(average_precision_score(y_true, y_score))
        try:
            out["brier"] = float(brier_score_loss(y_true, y_score))
            out["log_loss"] = float(log_loss(y_true, np.clip(y_score, 1e-6, 1 - 1e-6)))
        except ValueError:
            out["brier"] = None
            out["log_loss"] = None
    else:
        out["roc_auc"] = None
        out["pr_auc"] = None
        out["brier"] = None
        out["log_loss"] = None
        if y_score is not None and len(np.unique(y_true)) < 2:
            out["calibration_note"] = "Only one class present in y_true; ROC/PR/Brier omitted."
    return out


def majority_baseline(y_true) -> np.ndarray:
    y_true = np.asarray(y_true).astype(int)
    majority = 1 if y_true.mean() >= 0.5 else 0
    return np.full_like(y_true, majority)
