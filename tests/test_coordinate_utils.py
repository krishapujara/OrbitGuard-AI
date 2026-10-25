from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from backend.coordinate_utils import (
    datetime_to_julian,
    ensure_same_frame,
    julian_to_datetime,
    miss_distance,
    relative_position,
    relative_speed,
    relative_velocity,
    spherical_altitude_km,
)
from backend.exceptions import CoordinateError


def test_relative_geometry_units() -> None:
    r1 = (6378.0, 0.0, 0.0)
    r2 = (6378.0, 10.0, 0.0)
    dr = relative_position(r1, r2)
    assert miss_distance(dr) == pytest.approx(10.0)
    dv = relative_velocity((0.0, 7.0, 0.0), (0.0, 7.5, 0.0))
    assert relative_speed(dv) == pytest.approx(0.5)


def test_non_finite_rejected() -> None:
    with pytest.raises(CoordinateError):
        miss_distance((np.nan, 0.0, 0.0))


def test_frame_guard() -> None:
    assert ensure_same_frame("TEME", "TEME") == "TEME"
    with pytest.raises(CoordinateError):
        ensure_same_frame("TEME", "ITRF")


def test_spherical_altitude() -> None:
    alt = spherical_altitude_km((6878.137, 0.0, 0.0), 6378.137)
    assert alt == pytest.approx(500.0)


def test_julian_roundtrip() -> None:
    dt = datetime(2019, 12, 9, 16, 38, 29, tzinfo=timezone.utc)
    jd, fr = datetime_to_julian(dt)
    back = julian_to_datetime(jd, fr)
    assert abs((back - dt).total_seconds()) < 1.0
