from __future__ import annotations

import streamlit as st

from frontend.components import empty_state, metric_card


def render() -> None:
    st.header("Mission overview")
    st.caption(
        "Metrics come from the current backend screening run. "
        "Geometric close approach is not a collision prediction."
    )
    target = st.session_state.get("target")
    run = st.session_state.get("screening_run")
    if target is None:
        empty_state("Select a target satellite on the Satellite selection page to begin.")
        return
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Target", target.name, "Object name from the GP/TLE record")
        metric_card("Catalog ID", target.catalog_id, "NORAD catalog identifier")
    with c2:
        metric_card("Element epoch (UTC)", target.epoch_utc.strftime("%Y-%m-%d %H:%M"), "TLE/GP epoch")
        metric_card("Retrieved (UTC)", target.retrieved_at.strftime("%Y-%m-%d %H:%M"), "Network or upload time")
    with c3:
        cache_label = "cached" if target.from_cache else "fresh network/upload"
        metric_card("Data origin", cache_label, "Cached records remain labelled as cached")
        metric_card("Element age (h)", f"{target.element_age_hours():.2f}", "Now minus element epoch")
    with c4:
        horizon = st.session_state.get("horizon_hours", "—")
        metric_card("Forecast horizon (h)", str(horizon), "User-configured SGP4 window")
        metric_card("Validation", target.validation_status, "Parser/checksum status")

    if run is None:
        empty_state("No screening run yet. Open Conjunction screening and start a run.")
        return
    flagged = [a for a in run.approaches if a.within_threshold]
    nearest = run.approaches[0] if run.approaches else None
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        metric_card("Objects considered", str(run.objects_considered), "Includes the untruncated candidate list size")
        metric_card("Successfully propagated", str(run.objects_propagated), "Candidates with valid SGP4 samples")
    with d2:
        metric_card("Within threshold", str(len(flagged)), "Geometric screening flags, not collisions")
        metric_card("Approaches recorded", str(len(run.approaches)), "Nearest refined geometry per candidate")
    with d3:
        if nearest:
            metric_card("Min predicted sep (km)", f"{nearest.min_separation_km:.3f}", "Refined TEME miss distance")
            metric_card("Closest TCA (UTC)", nearest.tca_utc.strftime("%Y-%m-%d %H:%M:%S"), "Refined time of closest approach")
        else:
            metric_card("Min predicted sep (km)", "n/a", "No candidate geometry")
            metric_card("Closest TCA (UTC)", "n/a", None)
    with d4:
        metric_card("Propagation failures", str(run.objects_failed), "Candidates skipped due to SGP4 errors")
        metric_card("Screening status", "complete", "Run finished; see coverage notes")
    st.subheader("Coverage and limitations")
    for note in run.coverage_notes:
        st.write("- " + note)
    if run.failures:
        with st.expander(f"Failed objects ({len(run.failures)})"):
            st.dataframe(run.failures, use_container_width=True)
