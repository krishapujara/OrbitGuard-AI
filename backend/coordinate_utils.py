"""Relative geometry helpers. SGP4 states are compared only in TEME.

Units: position in kilometres, velocity in kilometres per second.
Frame: True Equator Mean Equinox (TEME), Earth-centered non-rotating, as
returned by the sgp4 package. TEME is not identical to GCRS/J2000 or ITRS.
This module does not convert TEME to Earth-fixed coordinates.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
from numpy.typing import NDArray

from backend.exceptions import CoordinateError

Array = NDArray[np.float64]

TEME_FRAME = "TEME"


def as_vector(values: tuple[float, float, float] | Array) -> Array:
    vec = np.asarray(values, dtype=np.float64).reshape(3)
    if not np.all(np.isfinite(vec)):
        raise CoordinateError("Non-finite vector components are not allowed.")
    return vec


def relative_position(r1: Array, r2: Array) -> Array:
    """dr = r2 - r1, kilometres, same frame."""
    return as_vector(r2) - as_vector(r1)


def relative_velocity(v1: Array, v2: Array) -> Array:
    """dv = v2 - v1, kilometres per second, same frame."""
    return as_vector(v2) - as_vector(v1)


def miss_distance(dr: Array) -> float:
    return float(np.linalg.norm(as_vector(dr)))


def relative_speed(dv: Array) -> float:
    return float(np.linalg.norm(as_vector(dv)))


def spherical_altitude_km(position_km: Array, earth_radius_km: float) -> float:
    return float(np.linalg.norm(as_vector(position_km)) - earth_radius_km)


def datetime_to_julian(dt: datetime) -> tuple[float, float]:
    """UTC datetime to Julian Date split (jd, fr) with jd at 0.5 day boundary."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    year, month, day = dt.year, dt.month, dt.day
    hour, minute, second = dt.hour, dt.minute, dt.second + dt.microsecond / 1e6
    from sgp4.api import jday

    jd, fr = jday(year, month, day, hour, minute, second)
    return float(jd), float(fr)


def julian_to_datetime(jd: float, fr: float = 0.0) -> datetime:
    """Inverse of datetime_to_julian using the same astronomical day numbering."""
    total = jd + fr
    # Algorithm from Meeus-style JD to Gregorian, valid for modern UTC dates.
    z = int(total + 0.5)
    f = (total + 0.5) - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    day_int = int(day)
    frac = day - day_int
    seconds = frac * 86400.0
    sec_int = int(round(seconds * 1e6) / 1e6)
    hours = int(seconds // 3600)
    seconds -= hours * 3600
    minutes = int(seconds // 60)
    seconds -= minutes * 60
    microseconds = int(round((seconds - int(seconds)) * 1e6))
    sec_whole = int(seconds)
    if microseconds >= 1_000_000:
        sec_whole += 1
        microseconds -= 1_000_000
    try:
        return datetime(year, month, day_int, hours, minutes, sec_whole, microseconds, tzinfo=timezone.utc)
    except ValueError as exc:
        raise CoordinateError(f"Invalid Julian date {jd}+{fr}") from exc


def ensure_same_frame(frame_a: str, frame_b: str) -> str:
    if frame_a != frame_b:
        raise CoordinateError(
            f"Cannot combine vectors from incompatible frames {frame_a} and {frame_b}."
        )
    return frame_a
