"""Geometric close-approach screening in TEME.

Coarse stage: uniform time samples of relative separation.
Refinement: bounded scalar minimization of range around each local minimum.
The coarse sample is never treated as the exact time of closest approach.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import numpy as np
from scipy.optimize import minimize_scalar

from backend.coordinate_utils import miss_distance, relative_position, relative_velocity, relative_speed
from backend.data_sources import freshness_warnings
from backend.exceptions import InvalidConfigurationError, PropagationError, ScreeningError
from backend.models import ApproachResult, OrbitalRecord, ScreeningRun
from backend.orbital_propagation import OrbitalPropagationService
from config.settings import Settings, get_settings

ASSUMPTIONS = [
    "States are SGP4/SDP4 TEME position/velocity in kilometres and kilometres per second.",
    "Closest approach is a geometric minimum of |r2-r1|; it is not a collision event.",
    "Public GP/TLE records do not include covariance, so this is screening, not Pc.",
    "A catalog subset or coarse filter may omit objects; coverage is not exhaustive.",
]


class ConjunctionScreeningService:
    def __init__(
        self,
        settings: Settings | None = None,
        propagator: OrbitalPropagationService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.propagator = propagator or OrbitalPropagationService()

    def validate_settings(self, horizon_hours: float, threshold_km: float, sample_seconds: float) -> None:
        if horizon_hours not in self.settings.allowed_horizons_hours:
            raise InvalidConfigurationError(
                f"Forecast horizon must be one of {self.settings.allowed_horizons_hours} hours."
            )
        if threshold_km <= 0 or threshold_km > 50_000:
            raise InvalidConfigurationError("Screening threshold must be a positive distance in kilometres.")
        if not (self.settings.min_sample_seconds <= sample_seconds <= self.settings.max_sample_seconds):
            raise InvalidConfigurationError(
                f"Sampling interval must be between {self.settings.min_sample_seconds} and "
                f"{self.settings.max_sample_seconds} seconds."
            )

    def screen(
        self,
        target: OrbitalRecord,
        candidates: list[OrbitalRecord],
        *,
        horizon_hours: float,
        threshold_km: float,
        sample_seconds: float,
        catalog_group: str | None = None,
        start: datetime | None = None,
        progress: Optional[Callable[[float, str], None]] = None,
        max_candidates: int | None = None,
    ) -> ScreeningRun:
        self.validate_settings(horizon_hours, threshold_km, sample_seconds)
        start = start or datetime.now(timezone.utc)
        stop = start + timedelta(hours=horizon_hours)
        max_candidates = max_candidates or self.settings.max_candidates
        considered = [c for c in candidates if c.catalog_id != target.catalog_id]
        skipped_self = len(candidates) - len(considered)
        truncated = 0
        if len(considered) > max_candidates:
            truncated = len(considered) - max_candidates
            considered = considered[:max_candidates]
        times = self.propagator.sample_interval(target, start, stop, sample_seconds)
        started = datetime.now(timezone.utc)
        try:
            t_r, t_v, _, valid_times = self.propagator.propagate_many(target, times)
        except PropagationError as exc:
            raise ScreeningError(f"Target satellite could not be propagated: {exc}") from exc
        if len(valid_times) < 3:
            raise ScreeningError("Target trajectory produced too few valid samples for screening.")

        approaches: list[ApproachResult] = []
        failures: list[dict[str, str]] = []
        propagated = 0
        failed = 0
        skipped = skipped_self
        coarse_margin = self.settings.coarse_margin
        for i, cand in enumerate(considered):
            if progress:
                progress((i + 1) / max(len(considered), 1), f"Screening {cand.name}")
            try:
                c_r, c_v, _, c_times = self.propagator.propagate_many(cand, valid_times)
            except PropagationError as exc:
                failed += 1
                failures.append({"catalog_id": cand.catalog_id, "name": cand.name, "error": str(exc)})
                continue
            # Align by timestamp intersection
            cmap = {t.isoformat(): idx for idx, t in enumerate(c_times)}
            idx_t = []
            idx_c = []
            aligned_times = []
            for j, t in enumerate(valid_times):
                k = cmap.get(t.isoformat())
                if k is None:
                    continue
                idx_t.append(j)
                idx_c.append(k)
                aligned_times.append(t)
            if len(aligned_times) < 3:
                skipped += 1
                failures.append(
                    {
                        "catalog_id": cand.catalog_id,
                        "name": cand.name,
                        "error": "Insufficient overlapping valid samples.",
                    }
                )
                continue
            tr = t_r[idx_t]
            tv = t_v[idx_t]
            cr = c_r[idx_c]
            cv = c_v[idx_c]
            dr = cr - tr
            dist = np.linalg.norm(dr, axis=1)
            propagated += 1
            min_coarse = float(np.min(dist))
            if min_coarse > threshold_km * coarse_margin:
                # Still report the refined global minimum so users see nearest geometry.
                result = self._refine_global(
                    target,
                    cand,
                    aligned_times,
                    tr,
                    tv,
                    cr,
                    cv,
                    dist,
                    horizon_hours,
                    threshold_km,
                    sample_seconds,
                    start,
                )
                result.screening_status = "outside_coarse_gate"
                result.warnings.append(
                    f"Coarse minimum {min_coarse:.3f} km exceeded {coarse_margin}× the "
                    f"{threshold_km:.1f} km threshold; other local minima were not exhaustively refined."
                )
                approaches.append(result)
                continue
            local_idx = local_minima_indices(dist)
            if not local_idx:
                local_idx = [int(np.argmin(dist))]
            best: ApproachResult | None = None
            for idx in local_idx:
                refined = self._refine_index(
                    target,
                    cand,
                    aligned_times,
                    idx,
                    horizon_hours,
                    threshold_km,
                    sample_seconds,
                    start,
                )
                if best is None or refined.min_separation_km < best.min_separation_km:
                    best = refined
            if best is not None:
                approaches.append(best)

        approaches.sort(key=lambda a: a.min_separation_km)
        finished = datetime.now(timezone.utc)
        notes = list(ASSUMPTIONS)
        if truncated:
            notes.append(
                f"Candidate list truncated to {max_candidates} objects; {truncated} were not screened. "
                "This run is not an exhaustive catalog search."
            )
        if catalog_group:
            notes.append(f"Candidates drawn from CelesTrak GROUP={catalog_group}.")
        notes.extend(freshness_warnings(target, horizon_hours))
        return ScreeningRun(
            target=target,
            horizon_hours=horizon_hours,
            threshold_km=threshold_km,
            sample_interval_seconds=sample_seconds,
            started_at=started,
            finished_at=finished,
            catalog_group=catalog_group,
            objects_considered=len(candidates),
            objects_propagated=propagated,
            objects_skipped=skipped,
            objects_failed=failed,
            approaches=approaches,
            failures=failures,
            coverage_notes=notes,
            from_cache_data=target.from_cache or any(c.from_cache for c in considered),
        )

    def _refine_global(
        self,
        target: OrbitalRecord,
        cand: OrbitalRecord,
        times: list[datetime],
        tr,
        tv,
        cr,
        cv,
        dist,
        horizon_hours: float,
        threshold_km: float,
        sample_seconds: float,
        start: datetime,
    ) -> ApproachResult:
        idx = int(np.argmin(dist))
        return self._refine_index(
            target, cand, times, idx, horizon_hours, threshold_km, sample_seconds, start
        )

    def _refine_index(
        self,
        target: OrbitalRecord,
        cand: OrbitalRecord,
        times: list[datetime],
        idx: int,
        horizon_hours: float,
        threshold_km: float,
        sample_seconds: float,
        start: datetime,
    ) -> ApproachResult:
        t0 = times[0]
        t_center = times[idx]
        span = sample_seconds
        t_lo = max(times[0], t_center - timedelta(seconds=span))
        t_hi = min(times[-1], t_center + timedelta(seconds=span))
        lo = (t_lo - t0).total_seconds()
        hi = (t_hi - t0).total_seconds()
        refinement_status = "brentq_range"

        def objective(seconds: float) -> float:
            when = t0 + timedelta(seconds=float(seconds))
            s1 = self.propagator.propagate(target, when)
            s2 = self.propagator.propagate(cand, when)
            dr = relative_position(s1.position_km, s2.position_km)
            return miss_distance(dr)

        try:
            if hi - lo < 1.0:
                raise ValueError("bracket too small")
            opt = minimize_scalar(objective, bounds=(lo, hi), method="bounded", options={"xatol": 0.05})
            if not opt.success:
                raise ValueError(opt.message)
            tca = t0 + timedelta(seconds=float(opt.x))
            min_sep = float(opt.fun)
            refinement_status = "converged"
        except (ValueError, PropagationError):
            tca = t_center
            s1c = self.propagator.propagate(target, tca)
            s2c = self.propagator.propagate(cand, tca)
            min_sep = miss_distance(relative_position(s1c.position_km, s2c.position_km))
            refinement_status = "coarse_fallback"

        s1 = self.propagator.propagate(target, tca)
        s2 = self.propagator.propagate(cand, tca)
        dr = relative_position(s1.position_km, s2.position_km)
        dv = relative_velocity(s1.velocity_km_s, s2.velocity_km_s)
        sep = miss_distance(dr)
        vrel = relative_speed(dv)
        within = sep <= threshold_km
        warnings = freshness_warnings(target, horizon_hours) + freshness_warnings(cand, horizon_hours)
        return ApproachResult(
            target_id=target.catalog_id,
            target_name=target.name,
            candidate_id=cand.catalog_id,
            candidate_name=cand.name,
            target_epoch_utc=target.epoch_utc,
            candidate_epoch_utc=cand.epoch_utc,
            target_age_hours=target.element_age_hours(start),
            candidate_age_hours=cand.element_age_hours(start),
            forecast_horizon_hours=horizon_hours,
            tca_utc=tca,
            min_separation_km=sep,
            relative_velocity_km_s=vrel,
            relative_position_km=(float(dr[0]), float(dr[1]), float(dr[2])),
            relative_velocity_vector_km_s=(float(dv[0]), float(dv[1]), float(dv[2])),
            screening_threshold_km=threshold_km,
            within_threshold=within,
            screening_status="within_threshold" if within else "outside_threshold",
            propagation_status="ok",
            refinement_status=refinement_status,
            sample_interval_seconds=sample_seconds,
            assumptions=list(ASSUMPTIONS),
            warnings=warnings,
        )


def local_minima_indices(dist: np.ndarray) -> list[int]:
    if dist.size < 3:
        return [int(np.argmin(dist))]
    idx = []
    for i in range(1, len(dist) - 1):
        if dist[i] <= dist[i - 1] and dist[i] <= dist[i + 1]:
            idx.append(i)
    return idx
