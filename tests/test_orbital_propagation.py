from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.exceptions import PropagationError
from backend.orbital_propagation import OrbitalPropagationService


def test_vanguard_sgp4_at_epoch(vanguard) -> None:
    """Vallado / python-sgp4 reference satellite 00005 at its TLE epoch."""
    service = OrbitalPropagationService()
    state = service.propagate(vanguard, vanguard.epoch_utc)
    assert state.frame == "TEME"
    assert state.error_code == 0
    # Published TEME kilometres from Vallado/sgp4 benchmark (tcppver.out sat 5 at epoch 0 min).
    assert state.position_km[0] == pytest.approx(7022.46529266, rel=1e-6, abs=1e-4)
    assert state.position_km[1] == pytest.approx(-1400.08296755, rel=1e-6, abs=1e-4)
    assert state.position_km[2] == pytest.approx(0.03995155, rel=1e-4, abs=1e-3)
    assert state.velocity_km_s[0] == pytest.approx(1.893841015, rel=1e-5, abs=1e-5)
    assert state.velocity_km_s[1] == pytest.approx(6.405893759, rel=1e-5, abs=1e-5)
    assert state.velocity_km_s[2] == pytest.approx(4.534807250, rel=1e-5, abs=1e-5)


def test_benchmark_88888_sgp4_at_epoch(benchmark_88888) -> None:
    """Space-Track Report No. 3 benchmark satellite 88888 at its TLE epoch."""
    service = OrbitalPropagationService()
    state = service.propagate(benchmark_88888, benchmark_88888.epoch_utc)
    assert state.frame == "TEME"
    assert state.error_code == 0
    # Space-Track Report No. 3 benchmark output (tsince = 0 min).
    assert state.position_km[0] == pytest.approx(2328.96975262, rel=1e-6, abs=1e-3)
    assert state.position_km[1] == pytest.approx(-5995.22051338, rel=1e-6, abs=1e-3)
    assert state.position_km[2] == pytest.approx(1719.97297192, rel=1e-6, abs=1e-3)
    assert state.velocity_km_s[0] == pytest.approx(2.912073281, rel=1e-5, abs=1e-4)
    assert state.velocity_km_s[1] == pytest.approx(-0.983417956, rel=1e-5, abs=1e-4)
    assert state.velocity_km_s[2] == pytest.approx(-7.090816210, rel=1e-5, abs=1e-4)


def test_iss_propagation_finite(iss) -> None:
    service = OrbitalPropagationService()
    when = datetime(2019, 12, 9, 18, 0, tzinfo=timezone.utc)
    state = service.propagate(iss, when)
    radius = sum(c * c for c in state.position_km) ** 0.5
    assert 6500 < radius < 7500
    speed = sum(c * c for c in state.velocity_km_s) ** 0.5
    assert 7.0 < speed < 8.2


def test_propagate_many_skips_nothing_at_valid_times(iss) -> None:
    service = OrbitalPropagationService()
    start = iss.epoch_utc
    times = service.sample_interval(iss, start, start, 60)
    r, v, err, valid = service.propagate_many(iss, times)
    assert len(valid) == len(times)
    assert r.shape[1] == 3
    assert v.shape[1] == 3
    assert set(err.tolist()) == {0}


def test_sample_interval_requires_positive_step(iss) -> None:
    service = OrbitalPropagationService()
    with pytest.raises(PropagationError):
        service.sample_interval(iss, iss.epoch_utc, iss.epoch_utc, 0)
