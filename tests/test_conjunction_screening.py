from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from backend.conjunction_screening import ConjunctionScreeningService, local_minima_indices
from backend.exceptions import InvalidConfigurationError


def test_local_minima() -> None:
    dist = np.array([5.0, 3.0, 4.0, 1.0, 2.0])
    assert local_minima_indices(dist) == [1, 3]


def test_screen_sample_catalog(sample_records) -> None:
    target = next(r for r in sample_records if r.catalog_id == "25544")
    service = ConjunctionScreeningService()
    start = datetime(2019, 12, 9, 17, 0, tzinfo=timezone.utc)
    run = service.screen(
        target,
        sample_records,
        horizon_hours=6,
        threshold_km=25.0,
        sample_seconds=120,
        start=start,
        max_candidates=10,
    )
    assert run.objects_propagated >= 1
    assert run.target.catalog_id == "25544"
    assert all(a.min_separation_km > 0 for a in run.approaches)
    assert all(a.refinement_status in {"converged", "coarse_fallback", "brentq_range"} for a in run.approaches)
    nearest = run.approaches[0]
    assert nearest.tca_utc.tzinfo is not None
    # Coarse sample is not silently treated as TCA without a refinement attempt.
    assert nearest.sample_interval_seconds == 120
    notes = " ".join(run.coverage_notes)
    assert "collision" in notes.lower() or "geometric" in notes.lower()


def test_invalid_horizon_rejected(iss, sample_records) -> None:
    service = ConjunctionScreeningService()
    with pytest.raises(InvalidConfigurationError):
        service.screen(
            iss,
            sample_records,
            horizon_hours=7,
            threshold_km=25.0,
            sample_seconds=60,
        )
