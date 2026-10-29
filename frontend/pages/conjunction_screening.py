from __future__ import annotations

import streamlit as st

from backend.conjunction_screening import ConjunctionScreeningService
from backend.exceptions import ModelUnavailableError, IncompatibleModelError, OrbitalGuardError
from backend.feature_engineering import FeatureEngineeringService
from backend.prediction_service import ModelPredictionService
from backend.risk_assessment import RiskAssessmentService
from config.settings import get_settings
from frontend.components import approach_detail, approaches_table, empty_state
from frontend.visualizations import relative_velocity_figure, separation_distribution, separation_figure


def render() -> None:
    st.header("Conjunction screening")
    st.caption(
        "SGP4 TEME geometry over a bounded horizon. Empty results do not prove that collision risk is absent; "
        "they mean no candidate in the screened subset fell inside the configured settings."
    )
    target = st.session_state.get("target")
    records = st.session_state.get("catalog_records") or []
    if target is None:
        empty_state("Select a target satellite first.")
        return
    settings = get_settings()
    horizon = st.selectbox("Forecast horizon (hours)", settings.allowed_horizons_hours, index=2)
    threshold = st.number_input("Geometric screening threshold (km)", min_value=0.1, max_value=5000.0, value=25.0, step=1.0)
    sample = st.slider(
        "Sampling interval (seconds)",
        min_value=settings.min_sample_seconds,
        max_value=settings.max_sample_seconds,
        value=settings.default_sample_seconds,
        step=10,
        help="Uniform coarse grid. Closest approach is refined around local minima; the grid sample is not the TCA.",
    )
    max_cands = st.slider("Maximum candidates", 10, settings.max_candidates, min(80, settings.max_candidates))
    st.session_state["horizon_hours"] = horizon
    col1, col2 = st.columns(2)
    start = col1.button("Start screening", type="primary")
    if col2.button("Refresh catalog then screen"):
        try:
            group = st.session_state.get("catalog_group", "stations")
            records = st.session_state["data_source"].fetch_group(group, refresh=True)
            st.session_state["catalog_records"] = records
            start = True
        except OrbitalGuardError as exc:
            st.error(str(exc))
            return
    if start:
        progress = st.progress(0.0, text="Starting...")
        def cb(frac: float, msg: str) -> None:
            progress.progress(min(1.0, frac), text=msg)
        try:
            run = ConjunctionScreeningService().screen(
                target,
                records,
                horizon_hours=float(horizon),
                threshold_km=float(threshold),
                sample_seconds=float(sample),
                catalog_group=st.session_state.get("catalog_group"),
                progress=cb,
                max_candidates=int(max_cands),
            )
            risk = RiskAssessmentService()
            for a in run.approaches:
                risk.annotate(a)
            _annotate_ml_proxy(target, records, run)
            st.session_state["screening_run"] = run
            st.session_state["screening_error"] = None
            progress.progress(1.0, text="Complete")
        except OrbitalGuardError as exc:
            st.session_state["screening_error"] = str(exc)
            st.error(str(exc))
            return
    if st.session_state.get("screening_error"):
        st.error(st.session_state["screening_error"])
    run = st.session_state.get("screening_run")
    if run is None:
        empty_state("No screening results yet.")
        return
    st.write(
        f"Considered {run.objects_considered}, propagated {run.objects_propagated}, "
        f"skipped {run.objects_skipped}, failed {run.objects_failed}."
    )
    table = approaches_table(run)
    if table.empty:
        st.info("No candidate approaches were recorded. This is not proof that no collision risk exists.")
        return
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        cand_search = st.text_input("Filter candidates by name or catalog ID", "", autocomplete="off")
    with col_f2:
        only_flagged = st.checkbox("Only show within-threshold flags")

    min_sep = st.slider("Filter: maximum displayed separation (km)", float(table["min_sep_km"].min()), float(table["min_sep_km"].max()), float(table["min_sep_km"].max()))
    view = table[table["min_sep_km"] <= min_sep]
    if only_flagged:
        view = view[view["within_threshold"]]
    if cand_search.strip():
        q = cand_search.strip().lower()
        view = view[view["candidate"].astype(str).str.lower().str.contains(q) | view["id"].astype(str).str.contains(q)]

    st.dataframe(view.sort_values("min_sep_km"), use_container_width=True, hide_index=True)
    visible_approaches = [a for a in run.approaches if a.candidate_id in set(view["id"])] if not view.empty else run.approaches
    labels = [f"{a.candidate_id} | {a.candidate_name} | {a.min_separation_km:.2f} km" for a in visible_approaches]
    pick = st.selectbox("Candidate detail", labels)
    approach = visible_approaches[labels.index(pick)]
    st.session_state["selected_approach"] = approach
    approach_detail(approach)
    st.plotly_chart(separation_distribution(list(table["min_sep_km"]), run.threshold_km), use_container_width=True)
    _plot_pair_series(target, approach)


def _annotate_ml_proxy(target, records, run) -> None:
    service = ModelPredictionService()
    if not service.available():
        return
    by_id = {r.catalog_id: r for r in records}
    features = FeatureEngineeringService()
    rows = []
    approaches = []
    for approach in run.approaches:
        cand = by_id.get(approach.candidate_id)
        if cand is None:
            continue
        rows.append(
            features.features_from_approach(target, cand, approach, at=run.started_at)
        )
        approaches.append(approach)
    if not rows:
        return
    try:
        scored = service.predict_rows(features.to_frame(rows))
    except (ModelUnavailableError, IncompatibleModelError):
        return
    for approach, score, label in zip(
        approaches, scored["ml_proxy_score"], scored["ml_proxy_label"]
    ):
        approach.ml_proxy_score = float(score)
        approach.ml_proxy_label = int(label)
    st.caption(
        "ML proxy scores are attached when a trusted local artifact exists. "
        "They estimate below_threshold_proxy, not collision probability."
    )


def _plot_pair_series(target, approach) -> None:
    from datetime import timedelta

    from backend.coordinate_utils import miss_distance, relative_position, relative_speed, relative_velocity
    from backend.orbital_propagation import OrbitalPropagationService
    from backend.exceptions import PropagationError

    records = st.session_state.get("catalog_records") or []
    cand = next((r for r in records if r.catalog_id == approach.candidate_id), None)
    if cand is None:
        return
    prop = OrbitalPropagationService()
    tca = approach.tca_utc
    times = [tca + timedelta(seconds=s) for s in range(-1800, 1801, 30)]
    dists = []
    speeds = []
    kept = []
    for t in times:
        try:
            s1 = prop.propagate(target, t)
            s2 = prop.propagate(cand, t)
        except PropagationError:
            continue
        dists.append(miss_distance(relative_position(s1.position_km, s2.position_km)))
        speeds.append(relative_speed(relative_velocity(s1.velocity_km_s, s2.velocity_km_s)))
        kept.append(t)
    if kept:
        st.plotly_chart(separation_figure(kept, dists, tca), use_container_width=True)
        st.plotly_chart(relative_velocity_figure(kept, speeds), use_container_width=True)
