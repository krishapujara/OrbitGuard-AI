"""Shared Streamlit widgets."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from backend.models import ApproachResult, OrbitalRecord, ScreeningRun


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def status_badge(text: str, kind: str = "info") -> None:
    mapping = {"ok": "success", "warn": "warning", "error": "error", "info": "info"}
    fn = getattr(st, mapping.get(kind, "info"))
    fn(text)


def record_preview(record: OrbitalRecord | None) -> None:
    if record is None:
        st.info("No satellite selected.")
        return
    age = record.element_age_hours()
    st.write(
        {
            "name": record.name,
            "catalog_id": record.catalog_id,
            "epoch_utc": record.epoch_utc.isoformat(),
            "retrieved_at": record.retrieved_at.isoformat(),
            "source": record.source,
            "source_url": record.source_url,
            "from_cache": record.from_cache,
            "validation": record.validation_status,
            "element_age_hours": round(age, 3),
            "inclination_deg": record.inclination_deg,
            "eccentricity": record.eccentricity,
            "mean_motion_rev_per_day": record.mean_motion_rev_per_day,
            "data_format": record.data_format,
        }
    )
    st.code(f"{record.line1}\n{record.line2}", language="text")
    if record.validation_messages:
        st.warning("Validation notes: " + "; ".join(record.validation_messages))


def approaches_table(run: ScreeningRun | None) -> pd.DataFrame:
    if run is None or not run.approaches:
        return pd.DataFrame()
    rows = []
    for a in run.approaches:
        rows.append(
            {
                "candidate": a.candidate_name,
                "id": a.candidate_id,
                "min_sep_km": round(a.min_separation_km, 3),
                "tca_utc": a.tca_utc.isoformat(),
                "v_rel_km_s": round(a.relative_velocity_km_s, 4),
                "threshold_km": a.screening_threshold_km,
                "within_threshold": a.within_threshold,
                "score": a.heuristic_score,
                "ml_proxy_score": a.ml_proxy_score,
                "target_age_h": round(a.target_age_hours, 2),
                "cand_age_h": round(a.candidate_age_hours, 2),
                "status": a.screening_status,
                "refinement": a.refinement_status,
            }
        )
    return pd.DataFrame(rows)


def approach_detail(approach: ApproachResult) -> None:
    st.subheader(f"{approach.candidate_name} ({approach.candidate_id})")
    st.write(
        {
            "tca_utc": approach.tca_utc.isoformat(),
            "min_separation_km": approach.min_separation_km,
            "relative_velocity_km_s": approach.relative_velocity_km_s,
            "relative_position_km_TEME": approach.relative_position_km,
            "screening_status": approach.screening_status,
            "refinement_status": approach.refinement_status,
            "heuristic_score": approach.heuristic_score,
            "ml_proxy_score": approach.ml_proxy_score,
            "ml_proxy_label": approach.ml_proxy_label,
            "collision_probability_status": approach.collision_probability_status,
        }
    )
    if approach.warnings:
        st.warning("\n".join(approach.warnings))
    with st.expander("Assumptions"):
        for item in approach.assumptions:
            st.write("- " + item)


def empty_state(message: str) -> None:
    st.info(message)
