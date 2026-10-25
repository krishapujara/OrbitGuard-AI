"""Features for the proxy ML task.

Prediction-time features are derived only from TLE fields and a single SGP4
evaluation at the screening start epoch. Refined miss distance and TCA are
labels or physical-baseline outputs, never input features.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from backend.coordinate_utils import miss_distance, relative_position, relative_speed, relative_velocity, spherical_altitude_km
from backend.exceptions import PropagationError
from backend.models import ApproachResult, OrbitalRecord
from backend.orbital_propagation import OrbitalPropagationService
from config.settings import get_settings

FEATURE_COLUMNS = [
    "target_inclination_deg",
    "candidate_inclination_deg",
    "rel_inclination_deg",
    "target_eccentricity",
    "candidate_eccentricity",
    "target_mean_motion",
    "candidate_mean_motion",
    "rel_mean_motion",
    "target_altitude_km",
    "candidate_altitude_km",
    "rel_altitude_km",
    "epoch_separation_km",
    "epoch_relative_speed_km_s",
    "target_age_hours",
    "candidate_age_hours",
    "forecast_horizon_hours",
    "sample_interval_seconds",
]

IDENTIFIER_COLUMNS = [
    "target_id",
    "candidate_id",
    "canonical_pair_id",
    "encounter_id",
    "target_epoch_utc",
    "candidate_epoch_utc",
]


class FeatureEngineeringService:
    def __init__(self, propagator: OrbitalPropagationService | None = None) -> None:
        self.propagator = propagator or OrbitalPropagationService()
        self.settings = get_settings()

    def features_from_records(
        self,
        target: OrbitalRecord,
        candidate: OrbitalRecord,
        *,
        at: datetime | None = None,
        horizon_hours: float,
        sample_seconds: float,
    ) -> dict:
        at = at or datetime.now(timezone.utc)
        tid = str(target.catalog_id)
        cid = str(candidate.catalog_id)
        canon = f"{min(tid, cid)}_{max(tid, cid)}"
        row: dict = {
            "target_id": target.catalog_id,
            "candidate_id": candidate.catalog_id,
            "canonical_pair_id": canon,
            "encounter_id": f"{target.catalog_id}-{candidate.catalog_id}-{int(at.timestamp())}",
            "target_epoch_utc": target.epoch_utc.isoformat(),
            "candidate_epoch_utc": candidate.epoch_utc.isoformat(),
            "target_inclination_deg": target.inclination_deg,
            "candidate_inclination_deg": candidate.inclination_deg,
            "rel_inclination_deg": _diff_deg(target.inclination_deg, candidate.inclination_deg),
            "target_eccentricity": target.eccentricity,
            "candidate_eccentricity": candidate.eccentricity,
            "target_mean_motion": target.mean_motion_rev_per_day,
            "candidate_mean_motion": candidate.mean_motion_rev_per_day,
            "rel_mean_motion": _sub(target.mean_motion_rev_per_day, candidate.mean_motion_rev_per_day),
            "target_age_hours": target.element_age_hours(at),
            "candidate_age_hours": candidate.element_age_hours(at),
            "forecast_horizon_hours": horizon_hours,
            "sample_interval_seconds": sample_seconds,
        }
        try:
            s1 = self.propagator.propagate(target, at)
            s2 = self.propagator.propagate(candidate, at)
            dr = relative_position(s1.position_km, s2.position_km)
            dv = relative_velocity(s1.velocity_km_s, s2.velocity_km_s)
            row["epoch_separation_km"] = miss_distance(dr)
            row["epoch_relative_speed_km_s"] = relative_speed(dv)
            row["target_altitude_km"] = spherical_altitude_km(
                np.array(s1.position_km), self.settings.earth_radius_km
            )
            row["candidate_altitude_km"] = spherical_altitude_km(
                np.array(s2.position_km), self.settings.earth_radius_km
            )
            row["rel_altitude_km"] = row["candidate_altitude_km"] - row["target_altitude_km"]
        except PropagationError:
            row["epoch_separation_km"] = None
            row["epoch_relative_speed_km_s"] = None
            row["target_altitude_km"] = None
            row["candidate_altitude_km"] = None
            row["rel_altitude_km"] = None
        return row

    def features_from_approach(
        self,
        target: OrbitalRecord,
        candidate: OrbitalRecord,
        approach: ApproachResult,
        *,
        at: datetime | None = None,
    ) -> dict:
        row = self.features_from_records(
            target,
            candidate,
            at=at,
            horizon_hours=approach.forecast_horizon_hours,
            sample_seconds=approach.sample_interval_seconds,
        )
        row["min_separation_km"] = approach.min_separation_km
        row["below_threshold_proxy"] = int(approach.within_threshold)
        row["coarse_epoch_below_threshold"] = int(
            (row.get("epoch_separation_km") or 1e9) <= approach.screening_threshold_km
        )
        return row

    def to_frame(self, rows: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(rows)
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        return df

    def leak_check_columns(self, columns: list[str]) -> list[str]:
        forbidden = {
            "min_separation_km",
            "tca_utc",
            "relative_velocity_km_s",
            "heuristic_score",
            "collision_probability",
            "below_threshold_proxy",
        }
        return [c for c in columns if c in forbidden]


def _sub(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def _diff_deg(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)
