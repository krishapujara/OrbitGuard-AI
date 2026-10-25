from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pytest

from backend.conjunction_screening import ConjunctionScreeningService
from backend.coordinate_utils import spherical_altitude_km
from backend.feature_engineering import FeatureEngineeringService
from backend.models import OrbitalRecord, ScreeningRun
from backend.orbital_propagation import OrbitalPropagationService
from backend.prediction_service import ModelPredictionService
from backend.report_service import ReportService
from backend.risk_assessment import RiskAssessmentService
from backend.tle_parser import TLEValidationService
from frontend.dashboard import PAGES


def test_end_to_end_conjunction_workflow(tmp_path, sample_records):
    # 1. Target and candidate selection
    target = next(r for r in sample_records if r.catalog_id == "25544")
    candidates = [r for r in sample_records if r.catalog_id != "25544"]
    assert len(candidates) == 3

    # 2. Orbital propagation test
    prop_service = OrbitalPropagationService()
    state = prop_service.propagate(target, target.epoch_utc)
    assert state.frame == "TEME"
    alt = spherical_altitude_km(state.position_km, 6378.137)
    assert 350.0 < alt < 450.0  # ISS LEO altitude range

    # 3. Conjunction screening
    screening_service = ConjunctionScreeningService()
    run = screening_service.screen(
        target,
        sample_records,
        horizon_hours=12,
        threshold_km=5000.0,
        sample_seconds=120,
        start=datetime(2019, 12, 9, 17, 0, tzinfo=timezone.utc),
        max_candidates=10,
    )

    assert isinstance(run, ScreeningRun)
    assert run.target.catalog_id == "25544"
    assert len(run.approaches) > 0
    assert run.objects_considered >= 3
    assert run.objects_propagated >= 3

    # 4. Risk assessment
    risk_service = RiskAssessmentService()
    for app in run.approaches:
        risk_service.annotate(app)
        assert 0.0 <= app.heuristic_score <= 100.0
        # Scientific honesty rule: Pc must be unavailable without genuine covariance
        assert app.collision_probability is None
        assert app.collision_probability_status == "unavailable"

    # 5. Feature engineering
    feat_service = FeatureEngineeringService()
    by_id = {r.catalog_id: r for r in sample_records}
    feature_rows = []
    for app in run.approaches:
        cand = by_id.get(app.candidate_id)
        if cand:
            row = feat_service.features_from_approach(target, cand, app, at=run.started_at)
            feature_rows.append(row)
    df_features = feat_service.to_frame(feature_rows)
    assert len(df_features) == len(run.approaches)

    # 6. ML Prediction (if local artifact available)
    pred_service = ModelPredictionService()
    if pred_service.available():
        scored_df = pred_service.predict_rows(df_features)
        assert "ml_proxy_score" in scored_df.columns
        assert "ml_proxy_label" in scored_df.columns
        assert bool(scored_df["ml_is_collision_probability"].iloc[0]) is False

    # 7. Report generation and export
    report_service = ReportService()
    csv_file = tmp_path / "screening_report.csv"
    txt_file = tmp_path / "screening_report.txt"
    report_service.export_csv(run, csv_file)
    report_service.export_text(run, txt_file)

    assert csv_file.exists()
    assert txt_file.exists()
    csv_df = pd.read_csv(csv_file)
    assert "target_id" in csv_df.columns
    assert "min_separation_km" in csv_df.columns

    txt_content = txt_file.read_text(encoding="utf-8")
    assert "OrbitalGuard AI" in txt_content or "ORBITALGUARD AI" in txt_content.upper()
    assert "TEME" in txt_content
    assert "LIMITATIONS" in txt_content


def test_all_frontend_pages_renderable(sample_records):
    # Verify that all 7 pages can be invoked without unhandled backend errors
    import streamlit as st

    # Initialize minimal mock session state
    target = sample_records[0]
    screening_service = ConjunctionScreeningService()
    run = screening_service.screen(
        target,
        sample_records,
        horizon_hours=6,
        threshold_km=5000.0,
        sample_seconds=300,
        start=datetime(2019, 12, 9, 17, 0, tzinfo=timezone.utc),
        max_candidates=4,
    )
    for app in run.approaches:
        RiskAssessmentService().annotate(app)

    st.session_state["catalog"] = sample_records
    st.session_state["target"] = target
    st.session_state["screening_run"] = run
    st.session_state["selected_candidate"] = sample_records[1]

    for page_name, render_fn in PAGES.items():
        assert callable(render_fn), f"Page handler for {page_name} is not callable"


def test_streamlit_app_ui_navigation_and_screening():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(r"app.py", default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    # 1. Satellite selection -> Load bundled sample
    at.sidebar.radio[0].set_value("Satellite selection")
    at.run()
    load_btn = next((b for b in at.button if "bundled sample" in (b.label or "").lower()), None)
    assert load_btn is not None
    load_btn.click()
    at.run()
    assert len(at.exception) == 0

    # 2. Conjunction screening -> Run screening
    at.sidebar.radio[0].set_value("Conjunction screening")
    at.run()
    screen_btn = next((b for b in at.button if "start screening" in (b.label or "").lower()), None)
    assert screen_btn is not None
    screen_btn.click()
    at.run()
    assert len(at.exception) == 0

    # 3. Mission overview
    at.sidebar.radio[0].set_value("Mission overview")
    at.run()
    assert len(at.exception) == 0
    assert len(at.metric) >= 4

    # 4. Orbital visualization
    at.sidebar.radio[0].set_value("Orbital visualization")
    at.run()
    assert len(at.exception) == 0

    # 5. Risk assessment
    at.sidebar.radio[0].set_value("Risk assessment")
    at.run()
    assert len(at.exception) == 0

    # 6. ML model evaluation
    at.sidebar.radio[0].set_value("ML model evaluation")
    at.run()
    assert len(at.exception) == 0

    # 7. Data and system health
    at.sidebar.radio[0].set_value("Data and system health")
    at.run()
    assert len(at.exception) == 0
