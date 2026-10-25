# Data dictionary

## OrbitalRecord (observed GP/TLE)

| Field | Unit / type | Meaning |
| --- | --- | --- |
| name | string | Object name from 3LE line 0 or UNKNOWN |
| catalog_id | string | NORAD catalog number; leading zeros stripped |
| line1, line2 | text | Validated TLE lines including checksum digit |
| epoch_utc | datetime UTC | Element epoch from line 1 |
| retrieved_at | datetime UTC | Network, cache, or upload time |
| source / source_url | string | Provenance |
| from_cache | bool | True if served from TTL cache |
| inclination_deg | deg | Line 2 inclination |
| eccentricity | — | Line 2 eccentricity |
| mean_motion_rev_per_day | rev/day | Line 2 mean motion |
| validation_status | enum | valid / valid_with_warnings |

## PropagationState (predicted)

TEME position kilometres, TEME velocity kilometres per second, UTC time, SGP4 error code.

## ApproachResult (predicted geometry)

| Field | Unit | Meaning |
| --- | --- | --- |
| tca_utc | UTC | Refined time of closest approach |
| min_separation_km | km | Refined TEME miss distance |
| relative_velocity_km_s | km/s | \|v₂ − v₁\| at TCA |
| within_threshold | bool | Geometric flag vs user threshold |
| heuristic_score | 0–100 | Ranking units, not probability |
| collision_probability | — | Always null for public TLE runs |
| ml_proxy_score | — | Optional P(below_threshold_proxy); not Pc |

## ScreeningRun

Counts of considered / propagated / skipped / failed objects, coverage notes, failures list, catalog group, settings.

## Proxy ML columns (`FEATURE_COLUMNS`)

Inclinations, eccentricities, mean motions, spherical altitudes at **screening start**, epoch separation and relative speed at start, element ages, horizon, sample interval. **Forbidden as features:** refined miss distance, TCA, heuristic score, Pc, `below_threshold_proxy` itself.
