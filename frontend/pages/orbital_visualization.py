from __future__ import annotations

from datetime import timedelta

import streamlit as st

from backend.exceptions import PropagationError
from backend.orbital_propagation import OrbitalPropagationService
from frontend.components import empty_state
from frontend.visualizations import orbit_figure


def render() -> None:
    st.header("Orbital visualization")
    st.caption(
        "All vectors are SGP4 TEME kilometres. Earth is a geometric sphere for scale, not a rotating ECEF globe. "
        "Trajectories are propagated predictions, not tracking observations."
    )
    target = st.session_state.get("target")
    run = st.session_state.get("screening_run")
    if target is None:
        empty_state("Select a target satellite first.")
        return
    records = st.session_state.get("catalog_records") or []
    approach = st.session_state.get("selected_approach")
    candidate = None
    if approach is not None:
        candidate = next((r for r in records if r.catalog_id == approach.candidate_id), None)
    if candidate is None and records:
        others = [r for r in records if r.catalog_id != target.catalog_id]
        names = [f"{r.catalog_id} | {r.name}" for r in others[:40]]
        if names:
            pick = st.selectbox("Candidate trajectory", names)
            candidate = others[names.index(pick)]
    horizon = float(st.session_state.get("horizon_hours") or 6)
    start = st.session_state.get("screening_run").started_at if run else None
    from datetime import datetime, timezone

    start = start or datetime.now(timezone.utc)
    n = st.slider("Trajectory samples", 20, 180, 80)
    times = [start + timedelta(hours=horizon * i / max(n - 1, 1)) for i in range(n)]
    idx = st.slider("Time index", 0, len(times) - 1, 0)
    selected = times[idx]
    st.write(f"Selected time (UTC): {selected.isoformat()} — propagated state, not an observation.")
    try:
        fig = orbit_figure(target, candidate, times, approach=approach, selected_time=selected)
        st.plotly_chart(fig, use_container_width=True)
        prop = OrbitalPropagationService()
        s = prop.propagate(target, selected)
        st.write(
            {
                "frame": s.frame,
                "target_position_km": s.position_km,
                "target_velocity_km_s": s.velocity_km_s,
            }
        )
    except PropagationError as exc:
        st.error(str(exc))
    st.info(
        "If a requested candidate cannot be propagated, its trajectory is omitted rather than fabricated."
    )
