"""Geometric proximity, heuristic ranking score, and collision-probability gate.

Public CelesTrak GP/TLE records do not include state covariance. This service
never invents covariance to produce a statistical collision probability.
"""

from __future__ import annotations

from backend.models import ApproachResult, CollisionProbabilityResult

# Heuristic score range: 0 to 100 (dimensionless ranking units, not probability).
# score = 100 * (0.70 * separation_term + 0.15 * velocity_term + 0.15 * freshness_term)
# separation_term = clip(1 - min_sep / threshold, 0, 1)
# velocity_term   = clip(v_rel / 15 km/s, 0, 1)   # 15 km/s is a typical LEO relative-speed scale
# freshness_term  = clip(1 - max(ages_h) / 72, 0, 1)
# Thresholds here are configurable ranking scales, not official safety standards.


SEPARATION_WEIGHT = 0.70
VELOCITY_WEIGHT = 0.15
FRESHNESS_WEIGHT = 0.15
VELOCITY_SCALE_KM_S = 15.0
FRESHNESS_SCALE_H = 72.0


class RiskAssessmentService:
    def geometric_proximity(self, approach: ApproachResult) -> dict:
        return {
            "min_separation_km": approach.min_separation_km,
            "tca_utc": approach.tca_utc.isoformat(),
            "relative_velocity_km_s": approach.relative_velocity_km_s,
            "threshold_km": approach.screening_threshold_km,
            "within_threshold": approach.within_threshold,
            "explanation": (
                "Geometric proximity compares the refined TEME miss distance with the "
                "user-configured screening threshold. A value inside the threshold is a "
                "close-approach candidate, not a demonstrated collision."
            ),
        }

    def heuristic_score(self, approach: ApproachResult) -> float:
        threshold = max(approach.screening_threshold_km, 1e-9)
        sep_term = _clip(1.0 - approach.min_separation_km / threshold, 0.0, 1.0)
        vel_term = _clip(approach.relative_velocity_km_s / VELOCITY_SCALE_KM_S, 0.0, 1.0)
        age = max(approach.target_age_hours, approach.candidate_age_hours)
        fresh_term = _clip(1.0 - age / FRESHNESS_SCALE_H, 0.0, 1.0)
        score = 100.0 * (
            SEPARATION_WEIGHT * sep_term + VELOCITY_WEIGHT * vel_term + FRESHNESS_WEIGHT * fresh_term
        )
        return float(round(score, 3))

    def annotate(self, approach: ApproachResult) -> ApproachResult:
        approach.heuristic_score = self.heuristic_score(approach)
        pc = self.collision_probability(approach)
        approach.collision_probability = pc.probability
        approach.collision_probability_status = pc.status
        return approach

    def collision_probability(
        self,
        approach: ApproachResult,
        *,
        covariance_available: bool = False,
        covariance_source: str | None = None,
        covariance_frame: str | None = None,
    ) -> CollisionProbabilityResult:
        if not covariance_available:
            return CollisionProbabilityResult(
                status="unavailable",
                probability=None,
                method=None,
                covariance_source=None,
                explanation=(
                    "Statistical collision probability is not computed because public TLE/GP "
                    "records do not provide state covariance. Encounter-plane Pc methods "
                    "(for example Alfano / Chan / Patera) require combined position uncertainty "
                    "in a documented frame, object sizes, and conjunction geometry. "
                    "OrbitalGuard AI will not manufacture covariance matrices."
                ),
            )
        if covariance_frame and covariance_frame.upper() not in {"TEME", "ITRF", "ECI", "RIC", "UVW"}:
            return CollisionProbabilityResult(
                status="unavailable",
                probability=None,
                explanation=f"Unsupported covariance frame {covariance_frame}.",
                covariance_source=covariance_source,
            )
        return CollisionProbabilityResult(
            status="unavailable",
            probability=None,
            explanation=(
                "A covariance flag was set, but this research prototype does not ingest an "
                "externally validated covariance product. Pc remains unavailable."
            ),
            covariance_source=covariance_source,
        )

    def explain(self, approach: ApproachResult) -> str:
        parts = [
            f"{approach.candidate_name} ({approach.candidate_id}) has a refined TEME miss "
            f"distance of {approach.min_separation_km:.3f} km at {approach.tca_utc.isoformat()} "
            f"with relative speed {approach.relative_velocity_km_s:.3f} km/s."
        ]
        if approach.within_threshold:
            parts.append(
                f"That separation is inside the {approach.screening_threshold_km:.1f} km "
                "geometric screening volume. This is a ranking flag, not a collision declaration."
            )
        else:
            parts.append(
                f"That separation is outside the {approach.screening_threshold_km:.1f} km "
                "screening volume for this run."
            )
        parts.append(
            f"Heuristic ranking score is {self.heuristic_score(approach):.1f} / 100 "
            "(not a probability)."
        )
        return " ".join(parts)


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
