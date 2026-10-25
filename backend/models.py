"""Typed records used across services."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class OrbitalRecord(BaseModel):
    name: str
    catalog_id: str
    line1: str
    line2: str
    epoch_utc: datetime
    retrieved_at: datetime
    source: str
    source_url: Optional[str] = None
    data_format: str = "TLE"
    validation_status: str = "valid"
    validation_messages: list[str] = Field(default_factory=list)
    classification: Optional[str] = None
    classification_source: Optional[str] = None
    from_cache: bool = False
    cache_retrieved_at: Optional[datetime] = None
    object_type: Optional[str] = None
    international_designator: Optional[str] = None
    mean_motion_rev_per_day: Optional[float] = None
    eccentricity: Optional[float] = None
    inclination_deg: Optional[float] = None
    raan_deg: Optional[float] = None
    arg_perigee_deg: Optional[float] = None
    mean_anomaly_deg: Optional[float] = None
    bstar: Optional[float] = None

    def element_age_hours(self, at: Optional[datetime] = None) -> float:
        now = at or datetime.now(timezone.utc)
        epoch = self.epoch_utc
        if epoch.tzinfo is None:
            epoch = epoch.replace(tzinfo=timezone.utc)
        return (now - epoch).total_seconds() / 3600.0


class PropagationState(BaseModel):
    time_utc: datetime
    position_km: tuple[float, float, float]
    velocity_km_s: tuple[float, float, float]
    frame: str = "TEME"
    error_code: int = 0


class ApproachResult(BaseModel):
    target_id: str
    target_name: str
    candidate_id: str
    candidate_name: str
    target_epoch_utc: datetime
    candidate_epoch_utc: datetime
    target_age_hours: float
    candidate_age_hours: float
    forecast_horizon_hours: float
    tca_utc: datetime
    min_separation_km: float
    relative_velocity_km_s: float
    relative_position_km: tuple[float, float, float]
    relative_velocity_vector_km_s: tuple[float, float, float]
    screening_threshold_km: float
    within_threshold: bool
    screening_status: str
    propagation_status: str
    refinement_status: str
    sample_interval_seconds: float
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    heuristic_score: Optional[float] = None
    collision_probability: Optional[float] = None
    collision_probability_status: str = "unavailable"
    ml_proxy_score: Optional[float] = None
    ml_proxy_label: Optional[int] = None


class ScreeningRun(BaseModel):
    target: OrbitalRecord
    horizon_hours: float
    threshold_km: float
    sample_interval_seconds: float
    started_at: datetime
    finished_at: datetime
    catalog_group: Optional[str] = None
    objects_considered: int = 0
    objects_propagated: int = 0
    objects_skipped: int = 0
    objects_failed: int = 0
    approaches: list[ApproachResult] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    coverage_notes: list[str] = Field(default_factory=list)
    from_cache_data: bool = False


class CollisionProbabilityResult(BaseModel):
    status: str
    probability: Optional[float] = None
    method: Optional[str] = None
    explanation: str
    covariance_source: Optional[str] = None
