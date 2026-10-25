from __future__ import annotations

import json

import streamlit as st

from backend.exceptions import IncompatibleModelError, ModelUnavailableError
from backend.prediction_service import ModelPredictionService
from frontend.components import empty_state
from frontend.visualizations import coefficient_bar, confusion_heatmap


def render() -> None:
    st.header("ML model evaluation")
    st.caption(
        "The trained task is below_threshold_proxy: whether refined SGP4 miss distance falls inside a geometric "
        "threshold. Model scores are not collision probabilities."
    )
    service = ModelPredictionService()
    status = service.status()
    if not status["available"]:
        empty_state(
            status["reason"]
            + " Physical screening still works. Training command: "
            "`python scripts/download_catalog.py` then `python -m ml.train_baseline --build-if-missing`."
        )
        st.write(
            {
                "prediction_target": "below_threshold_proxy (not collision)",
                "why_untrained": (
                    "A defensible collision-labelled dataset is not shipped. The optional pipeline "
                    "builds proxy labels from SGP4 screening of a local catalog snapshot."
                ),
            }
        )
        return
    try:
        _, meta = service.load()
    except (ModelUnavailableError, IncompatibleModelError) as exc:
        st.error(str(exc))
        return
    st.write(
        {
            "available": True,
            "model_type": meta.get("model_type"),
            "target_definition": meta.get("target_definition"),
            "target_description": meta.get("target_description"),
            "training_timestamp": meta.get("training_timestamp"),
            "dataset": meta.get("training_dataset_version"),
            "split": meta.get("split"),
        }
    )
    test = (meta.get("metrics") or {}).get("test") or {}
    if not test:
        st.warning("Metadata does not contain test metrics; none are displayed.")
        return
    st.subheader("Test-set comparison")
    cols = st.columns(3)
    for i, key in enumerate(("ml", "physical_epoch_threshold", "dummy_majority")):
        block = test.get(key) or {}
        with cols[i]:
            st.markdown(f"**{key}**")
            st.write(
                {
                    "precision": block.get("precision"),
                    "recall": block.get("recall"),
                    "f1": block.get("f1"),
                    "accuracy": block.get("accuracy"),
                    "prevalence_positive": block.get("prevalence_positive"),
                }
            )
    st.write(meta.get("ml_improves_physical_baseline"))
    ml_block = test.get("ml") or {}
    if ml_block.get("confusion_matrix"):
        st.plotly_chart(confusion_heatmap(ml_block["confusion_matrix"]), use_container_width=True)
    if ml_block.get("brier") is not None:
        st.write({"brier": ml_block.get("brier"), "log_loss": ml_block.get("log_loss"), "roc_auc": ml_block.get("roc_auc"), "pr_auc": ml_block.get("pr_auc")})
        st.caption("These calibration/discrimination numbers apply to the proxy label, not collision probability.")
    coef = meta.get("feature_coefficients") or []
    if coef:
        st.plotly_chart(coefficient_bar(coef[:16]), use_container_width=True)
    st.subheader("Limitations")
    for item in meta.get("limitations") or []:
        st.write("- " + item)
    with st.expander("Raw metadata"):
        st.code(json.dumps({k: v for k, v in meta.items() if k != "feature_coefficients"}, indent=2)[:8000])
