"""SGP4 propagation wrapper (Vallado / python-sgp4 TEME states).

SGP4/SDP4 is a mean-element analytic propagator consistent with NORAD GP
element sets. It is not a high-fidelity numerical force model and is not a
learned model of future gravity or drag.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
from numpy.typing import NDArray
from sgp4.api import SGP4_ERRORS, Satrec

from backend.coordinate_utils import datetime_to_julian
from backend.exceptions import InvalidOrbitalRecordError, PropagationError
from backend.models import OrbitalRecord, PropagationState

TEME = "TEME"


class OrbitalPropagationService:
    def initialize(self, record: OrbitalRecord) -> Satrec:
        try:
            sat = Satrec.twoline2rv(record.line1, record.line2)
        except Exception as exc:  # sgp4 may raise ValueError
            raise InvalidOrbitalRecordError(
                f"SGP4 could not initialize {record.name} ({record.catalog_id}): {exc}"
            ) from exc
        return sat

    def propagate(self, record: OrbitalRecord, when: datetime) -> PropagationState:
        sat = self.initialize(record)
        return self._propagate_sat(sat, record, when)

    def propagate_many(
        self, record: OrbitalRecord, times: list[datetime]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.int32], list[datetime]]:
        sat = self.initialize(record)
        jd = np.empty(len(times), dtype=np.float64)
        fr = np.empty(len(times), dtype=np.float64)
        for i, t in enumerate(times):
            jd[i], fr[i] = datetime_to_julian(t)
        err, r, v = sat.sgp4_array(jd, fr)
        err = np.asarray(err, dtype=np.int32)
        r = np.asarray(r, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        ok = (err == 0) & np.isfinite(r).all(axis=1) & np.isfinite(v).all(axis=1)
        if not np.any(ok):
            code = int(err[0]) if len(err) else -1
            raise PropagationError(
                f"SGP4 failed for {record.name} ({record.catalog_id}): {self.error_message(code)}"
            )
        valid_times = [t for t, flag in zip(times, ok) if flag]
        return r[ok], v[ok], err, valid_times

    def _propagate_sat(self, sat: Satrec, record: OrbitalRecord, when: datetime) -> PropagationState:
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        jd, fr = datetime_to_julian(when)
        code, position, velocity = sat.sgp4(jd, fr)
        pos = np.asarray(position, dtype=np.float64)
        vel = np.asarray(velocity, dtype=np.float64)
        if code != 0:
            raise PropagationError(
                f"SGP4 error {code} for {record.name} ({record.catalog_id}): {self.error_message(code)}"
            )
        if not np.all(np.isfinite(pos)) or not np.all(np.isfinite(vel)):
            raise PropagationError(
                f"Non-finite TEME state for {record.name} ({record.catalog_id}) at {when.isoformat()}."
            )
        return PropagationState(
            time_utc=when.astimezone(timezone.utc),
            position_km=(float(pos[0]), float(pos[1]), float(pos[2])),
            velocity_km_s=(float(vel[0]), float(vel[1]), float(vel[2])),
            frame=TEME,
            error_code=0,
        )

    def sample_interval(
        self, record: OrbitalRecord, start: datetime, stop: datetime, step_seconds: float
    ) -> list[datetime]:
        if step_seconds <= 0:
            raise PropagationError("Sampling interval must be positive.")
        times = []
        t = start
        delta = timedelta(seconds=step_seconds)
        while t <= stop:
            times.append(t)
            t = t + delta
        if not times or times[-1] < stop:
            times.append(stop)
        return times

    @staticmethod
    def error_message(code: int) -> str:
        return SGP4_ERRORS.get(code, f"unknown SGP4 error {code}")
