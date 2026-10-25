# Architecture

OrbitalGuard AI is a local Streamlit application with a scientific backend. There is no remote inference API.

```
CelesTrak GP / upload / bundled sample
        │
        ▼
 TLEValidationService  →  OrbitalRecord (checksum, epoch, elements)
        │
        ▼
 DataSourceService (HTTP retries, SHA-256 cache, manifests)
        │
        ▼
 OrbitalPropagationService (sgp4 Satrec, TEME km / km/s)
        │
        ▼
 ConjunctionScreeningService (coarse |r2-r1|, local minima, bounded refine)
        │
        ├── RiskAssessmentService (geometry + heuristic 0–100; Pc gated)
        ├── FeatureEngineeringService (epoch-only features; no TCA leak)
        └── ReportService (CSV / text with provenance)
```

## Coordinate policy

All pairwise geometry is computed in **TEME** as returned by python-sgp4. The UI does not convert TEME to ITRF/ECEF. Earth in the 3D plot is a sphere for scale, not a rotating globe.

## Screening

1. Uniform time grid over a bounded horizon (6–72 h).
2. Relative range on that grid is a **coarse** signal.
3. Local minima are refined with `scipy.optimize.minimize_scalar` (bounded).
4. If the coarse minimum is far outside `coarse_margin × threshold`, only the global coarse minimum is refined.

Candidate lists may be truncated (`max_candidates`). Coverage notes always state that the search is not exhaustive.

## ML (optional)

Labels are `below_threshold_proxy` from the same SGP4 screening, not observed collisions. Training uses grouped chronological holdout on `candidate_id`. Artifacts must set `trusted_origin = orbitalguard-ai-local` or they are refused.
