# Limitations

- Public GP/TLE coverage is incomplete and delayed.
- SGP4 TEME geometry is approximate; error grows with element age and horizon.
- Geometric TCA ≠ collision.
- Statistical Pc is unavailable without covariance, sizes, and a documented encounter-plane method.
- Heuristic scores are ranking aids (weights 0.70 / 0.15 / 0.15), not safety standards.
- Candidate truncation and catalog subsets omit objects; empty results are not proof of safety.
- Cached records remain labelled cached; they are never displayed as live.
- The 3D Earth is a sphere in TEME, not ECEF ground track.
- Optional ML uses proxy labels from the same snapshot; it is not a collision classifier.
- Development was exercised on Python 3.13 when 3.11/3.12 were unavailable on the implementation machine (`requirements.txt` notes this).
