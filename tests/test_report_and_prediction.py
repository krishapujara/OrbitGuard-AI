from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from backend.exceptions import ModelUnavailableError
from backend.prediction_service import ModelPredictionService
from backend.report_service import ReportService
from backend.risk_assessment import RiskAssessmentService
from frontend.dashboard import PAGES
from frontend.visualizations import orbit_figure


def test_report_export(tmp_path, sample_records) -> None:
    from backend.conjunction_screening import ConjunctionScreeningService

    target = next(r for r in sample_records if r.catalog_id == "25544")
    run = ConjunctionScreeningService().screen(
        target,
        sample_records,
        horizon_hours=6,
        threshold_km=50.0,
        sample_seconds=180,
        start=datetime(2019, 12, 9, 17, tzinfo=timezone.utc),
        max_candidates=4,
    )
    RiskAssessmentService()
    csv_path = tmp_path / "run.csv"
    txt_path = tmp_path / "run.txt"
    ReportService().export_csv(run, csv_path)
    ReportService().export_text(run, txt_path)
    df = pd.read_csv(csv_path)
    assert "min_separation_km" in df.columns
    text = txt_path.read_text(encoding="utf-8")
    assert "TEME" in text
    assert "collision probability" in text.lower() or "covariance" in text.lower()


def test_prediction_service_missing_artifact(tmp_path) -> None:
    service = ModelPredictionService(artifact_dir=tmp_path)
    assert service.available() is False
    with pytest.raises(ModelUnavailableError):
        service.load()


def test_dashboard_pages_registered() -> None:
    expected = {
        "Mission overview",
        "Satellite selection",
        "Conjunction screening",
        "Orbital visualization",
        "Risk assessment",
        "ML model evaluation",
        "Data and system health",
    }
    assert set(PAGES) == expected


def test_orbit_figure_teme_labels(iss, sample_records) -> None:
    cand = next(r for r in sample_records if r.catalog_id == "20580")
    times = [datetime(2019, 12, 9, 17, tzinfo=timezone.utc)]
    fig = orbit_figure(iss, cand, times, selected_time=times[0])
    assert "TEME" in fig.layout.scene.xaxis.title.text
    names = [t.name for t in fig.data]
    assert any("not an observation" in (t.name or "").lower() or "SGP4 TEME" in (t.name or "") for t in fig.data)
    assert names
