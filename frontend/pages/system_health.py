from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from backend.prediction_service import ModelPredictionService
from backend.report_service import ReportService
from config.settings import get_settings
from frontend.components import empty_state


def render() -> None:
    st.header("Data and system health")
    settings = get_settings()
    service = st.session_state["data_source"]
    target = st.session_state.get("target")
    run = st.session_state.get("screening_run")
    col1, col2 = st.columns(2)
    if col1.button("Refresh diagnostics"):
        st.session_state["health_checked_at"] = datetime.now(timezone.utc).isoformat()
    if col2.button("Ping CelesTrak stations (network)"):
        try:
            recs = service.fetch_group("stations", refresh=True)
            st.success(f"CelesTrak reachable. Retrieved {len(recs)} STATIONS records.")
            st.session_state["last_successful_retrieval"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            st.error(str(exc))
            st.session_state["last_data_error"] = str(exc)

    st.subheader("Application")
    st.write(
        {
            "name": settings.app_name,
            "version": settings.app_version,
            "python_ui": "Streamlit",
            "checked_at": st.session_state.get("health_checked_at"),
        }
    )
    st.subheader("Catalog cache")
    cache_rows = service.cache_status()
    if cache_rows:
        st.dataframe(cache_rows, use_container_width=True)
    else:
        empty_state("No cache files yet.")
    st.subheader("Current target")
    if target:
        st.write(
            {
                "name": target.name,
                "catalog_id": target.catalog_id,
                "epoch_utc": target.epoch_utc.isoformat(),
                "retrieved_at": target.retrieved_at.isoformat(),
                "from_cache": target.from_cache,
                "validation": target.validation_status,
                "element_age_hours": target.element_age_hours(),
            }
        )
    else:
        empty_state("No target selected.")
    st.subheader("Screening")
    if run:
        st.write(
            {
                "objects_considered": run.objects_considered,
                "objects_propagated": run.objects_propagated,
                "objects_failed": run.objects_failed,
                "started_at": run.started_at.isoformat(),
                "finished_at": run.finished_at.isoformat(),
            }
        )
        if st.button("Export CSV and text report"):
            try:
                csv_path = ReportService().export_csv(run)
                txt_path = ReportService().export_text(run)
                st.success(f"Wrote {csv_path.name} and {txt_path.name} under data/processed.")
                st.download_button("Download CSV", csv_path.read_text(encoding="utf-8"), file_name=csv_path.name)
                st.download_button("Download text report", txt_path.read_text(encoding="utf-8"), file_name=txt_path.name)
            except Exception as exc:
                st.error(f"Report export failed: {exc}")
    else:
        empty_state("No screening run in this session.")
    st.subheader("Model artifact")
    st.write(ModelPredictionService().status())
    st.subheader("Recent safe error messages")
    for key in ("last_data_error", "screening_error"):
        msg = st.session_state.get(key)
        if msg:
            st.warning(f"{key}: {msg}")
    if not st.session_state.get("last_data_error") and not st.session_state.get("screening_error"):
        st.info("No stored UI errors in this session.")
    st.caption("Environment variables and stack traces are not displayed.")
