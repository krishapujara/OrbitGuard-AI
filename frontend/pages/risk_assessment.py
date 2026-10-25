from __future__ import annotations

import streamlit as st

from backend.risk_assessment import (
    FRESHNESS_SCALE_H,
    FRESHNESS_WEIGHT,
    SEPARATION_WEIGHT,
    VELOCITY_SCALE_KM_S,
    VELOCITY_WEIGHT,
    RiskAssessmentService,
)
from frontend.components import empty_state


def render() -> None:
    st.header("Risk assessment")
    st.caption("Three separate concepts: geometry, a ranking heuristic, and statistical Pc (usually unavailable).")
    approach = st.session_state.get("selected_approach")
    run = st.session_state.get("screening_run")
    if approach is None and run and run.approaches:
        approach = run.approaches[0]
        st.session_state["selected_approach"] = approach
    if approach is None:
        empty_state("Run screening and select a candidate first.")
        return
    service = RiskAssessmentService()
    service.annotate(approach)

    st.subheader("1. Geometric proximity")
    geo = service.geometric_proximity(approach)
    st.write(geo)
    if approach.within_threshold:
        st.warning(
            "Predicted TEME miss distance is inside the user threshold. "
            "This is a geometric flag, not a collision."
        )
    else:
        st.success("Predicted TEME miss distance is outside the user threshold for this run.")

    st.subheader("2. Heuristic screening score")
    st.write(
        {
            "score": approach.heuristic_score,
            "range": "0 to 100 ranking units",
            "formula": (
                f"100 * ({SEPARATION_WEIGHT}*clip(1-d/threshold,0,1) + "
                f"{VELOCITY_WEIGHT}*clip(v_rel/{VELOCITY_SCALE_KM_S},0,1) + "
                f"{FRESHNESS_WEIGHT}*clip(1-age/{FRESHNESS_SCALE_H},0,1))"
            ),
            "not_a_probability": True,
            "not_an_official_safety_standard": True,
        }
    )

    st.subheader("3. Statistical collision probability")
    pc = service.collision_probability(approach)
    st.error(pc.explanation) if pc.status == "unavailable" else st.write(pc.model_dump())
    st.metric("Pc status", pc.status)
    st.metric("Pc value", "unavailable" if pc.probability is None else str(pc.probability))

    st.subheader("4. Optional ML proxy score")
    if approach.ml_proxy_score is None:
        st.info(
            "No trusted local model artifact is loaded, so no ML proxy score is shown. "
            "Physical SGP4 screening above does not depend on ML."
        )
    else:
        st.write(
            {
                "ml_proxy_score": approach.ml_proxy_score,
                "ml_proxy_label": approach.ml_proxy_label,
                "target": "below_threshold_proxy",
                "is_collision_probability": False,
            }
        )

    st.subheader("Plain-language explanation")
    st.write(service.explain(approach))
    st.info("A high heuristic score does not display a collision-alert badge.")
