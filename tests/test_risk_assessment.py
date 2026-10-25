from __future__ import annotations

from datetime import datetime, timezone

from backend.models import ApproachResult
from backend.risk_assessment import RiskAssessmentService


def _approach(**kwargs) -> ApproachResult:
    now = datetime(2019, 12, 9, 18, tzinfo=timezone.utc)
    payload = dict(
        target_id="25544",
        target_name="ISS",
        candidate_id="20580",
        candidate_name="HST",
        target_epoch_utc=now,
        candidate_epoch_utc=now,
        target_age_hours=12.0,
        candidate_age_hours=12.0,
        forecast_horizon_hours=24.0,
        tca_utc=now,
        min_separation_km=10.0,
        relative_velocity_km_s=10.0,
        relative_position_km=(10.0, 0.0, 0.0),
        relative_velocity_vector_km_s=(10.0, 0.0, 0.0),
        screening_threshold_km=25.0,
        within_threshold=True,
        screening_status="within_threshold",
        propagation_status="ok",
        refinement_status="converged",
        sample_interval_seconds=60.0,
    )
    payload.update(kwargs)
    return ApproachResult(**payload)


def test_heuristic_score_range_and_weights() -> None:
    service = RiskAssessmentService()
    close = service.heuristic_score(_approach(min_separation_km=0.0, relative_velocity_km_s=15.0, target_age_hours=0, candidate_age_hours=0))
    far = service.heuristic_score(_approach(min_separation_km=100.0, relative_velocity_km_s=0.0, target_age_hours=72, candidate_age_hours=72, within_threshold=False))
    assert 0 <= far < close <= 100
    assert close == 100.0
    assert far == 0.0


def test_collision_probability_unavailable_without_covariance() -> None:
    service = RiskAssessmentService()
    result = service.collision_probability(_approach())
    assert result.status == "unavailable"
    assert result.probability is None
    assert "covariance" in result.explanation.lower()


def test_annotate_does_not_invent_pc() -> None:
    service = RiskAssessmentService()
    annotated = service.annotate(_approach())
    assert annotated.heuristic_score is not None
    assert annotated.collision_probability is None
    assert annotated.collision_probability_status == "unavailable"
