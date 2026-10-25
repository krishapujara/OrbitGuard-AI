# OrbitalGuard AI ? Comprehensive Project Audit Report

**Audit Date:** October 14, 2026  
**Auditor Roles:** Senior Aerospace Software Engineer, Orbital Mechanics Specialist, Machine Learning Auditor, Software QA Engineer, UI/UX Auditor  
**Project Workspace:** `C:\Users\DELL\orbitalguard-ai`  
**Execution Environment:** Windows 11, Python 3.13.5 (Anaconda), Streamlit 1.45.1, SGP4 2.27, Scikit-learn 1.6.1, Pytest 8.3.4  
**Audit Status:** COMPLETE ? All Findings Categorized and Validated

---

## 1. Executive Summary & Audit Verdict

OrbitalGuard AI was subjected to an exhaustive scientific, architectural, algorithmic, machine-learning, user-interface, and documentation audit. Every source file, configuration setting, test suite, and data artifact was inspected through direct code inspection and runtime execution.

### Key Audit Achievements:
1. **Orbital Mechanics & SGP4 Ground Truth:** Corrected the test benchmark mismatch between Vanguard 1 (`00005`) and benchmark satellite `88888`. Verified propagation in True Equator Mean Equinox (TEME) coordinates against official David Vallado SGP4 benchmarks (`tcppver.out`).
2. **TLE Blank-Line Ingestion:** Discovered and fixed an issue where blank lines between TLE lines/names caused valid catalog files to be rejected.
3. **Machine Learning Data Leakage Elimination:** Discovered that reverse-ordered satellite pairs (e.g. Target A vs Candidate B and Target B vs Candidate A) could leak across splits. Implemented canonical pair deduplication `(min(id1, id2), max(id1, id2))` to eliminate reverse-pair leakage.
4. **Plotly Visualization Bug Fixed:** Discovered and resolved a Plotly `add_vline` runtime exception when handling Python `datetime` objects on x-axes, restoring error-free rendering of closest-approach time markers.
5. **Full Test Suite & Headless UI Verification:** Implemented missing test files (`test_dataset_pipeline.py`, `test_model_validation.py`, and `test_integration.py` including `streamlit.testing.v1.AppTest`), bringing the automated test suite to **48 passing tests (100% pass rate)**.
6. **Artifact Synchronization:** Unified and synchronized local model artifacts across both `ml/artifacts/` and `models/artifacts/`.

---

## 2. Real Architecture & Execution Dependency Map

```
[User / CLI / Streamlit UI]
        ?
        ??? 1. Data Selection (Satellite Selection Page / scripts/download_catalog.py)
        ?      ??? Live CelesTrak Query (GET celestrak.org/NORAD/elements/gp.php)
        ?      ??? Local Disk Cache (data/cache/ [SHA-256 URL hash + TTL])
        ?      ??? Custom TLE File Upload (UTF-8 stream validation)
        ?      ??? Offline Bundled Catalog (data/sample_metadata/sample_catalog.tle)
        ?
        ??? 2. TLE Parsing & Validation (backend/tle_parser.py)
        ?      ??? Strip blank lines & normalize record blocks
        ?      ??? Modulo-10 checksum calculation (columns 1-68)
        ?      ??? Matching NORAD catalog identifiers across Line 1 and Line 2
        ?      ??? UTC epoch translation (fractional day of year -> datetime)
        ?
        ??? 3. Orbital Propagation (backend/orbital_propagation.py)
        ?      ??? Satrec twoline2rv initialization
        ?      ??? SGP4 / SDP4 analytical propagation
        ?      ??? Output: TEME frame position (km) and velocity (km/s)
        ?
        ??? 4. Conjunction Screening (backend/conjunction_screening.py)
        ?      ??? Coarse uniform time sampling (6h, 12h, 24h, 48h, 72h)
        ?      ??? Euclidean miss distance calculation dr = r2 - r1
        ?      ??? Local minima detection
        ?      ??? Bounded Golden-Section scalar minimization of range -> Refined TCA & miss distance
        ?
        ??? 5. Risk Assessment (backend/risk_assessment.py)
        ?      ??? Concept 1: Geometric Proximity (refined separation <= threshold)
        ?      ??? Concept 2: Heuristic Ranking Score (0 to 100, weighted 70/15/15)
        ?      ??? Concept 3: Statistical Pc Gate (UNAVAILABLE without genuine covariance)
        ?
        ??? 6. Feature Engineering & ML Pipeline (backend/feature_engineering.py & ml/)
        ?      ??? Kinematic features strictly available at start epoch (t0)
        ?      ??? Deduplicated canonical pair tracking (min_id, max_id)
        ?      ??? Grouped chronological holdout split (ml/validation.py)
        ?      ??? SimpleImputer -> StandardScaler -> LogisticRegression (ml/train_baseline.py)
        ?      ??? Prediction Service (backend/prediction_service.py) -> ml_proxy_score
        ?
        ??? 7. Presentation & Export (frontend/ & backend/report_service.py)
               ??? 7 Streamlit Pages (Mission Overview, Selection, Screening, 3D Plotly, Risk, ML, Health)
               ??? Report Exporter -> CSV spreadsheet and TXT audit report
```

---

## 3. Detailed Audit Findings & Status Matrix

| ID | Module / Area | Finding Description | Severity | Status | Evidence & Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUD-01** | `sgp4` Package | Missing dependency in local Python environment during preflight. | High | **FIXED** | Installed `sgp4==2.27` via pip. Preflight script confirmed `OK sgp4 2.27`. |
| **AUD-02** | `test_orbital_propagation.py` | Reference test `test_vanguard_sgp4_at_epoch` was asserting Space-Track Report No. 3 benchmark sat 88888 coordinates against Vanguard 1 (sat 00005). | High | **FIXED** | Discovered root cause via `sgp4/tcppver.out`. Updated assertions for sat 5 to benchmark values `[7022.465, -1400.083, 0.040]` km and added a dedicated test for sat 88888 `[2328.970, -5995.221, 1719.973]` km. |
| **AUD-03** | `backend/tle_parser.py` | `parse_text` assumed adjacent lines without empty lines. When CelesTrak responses contained `

` or blank lines between name and line 1, records were rejected. | Medium | **FIXED** | Filtered lines at start of `parse_text`: `lines = [line.strip() for line in text.splitlines() if line.strip()]`. Successfully parsed all 155 records from CelesTrak `visual` group. |
| **AUD-04** | `frontend/visualizations.py` | In `separation_figure`, `fig.add_vline(x=tca, ...)` crashed with `TypeError: unsupported operand type(s) for +: 'int' and 'datetime.datetime'` due to an upstream Plotly bug when `x` is a datetime. | High | **FIXED** | Replaced `add_vline` with `fig.add_shape(type='line', x0=tca, x1=tca, y0=0, y1=1, yref='paper', ...)` and `fig.add_annotation(...)`. Verified runtime rendering with 0 errors. |
| **AUD-05** | `ml/build_dataset.py` & Leakage | Multi-target screening produced reverse-ordered duplicates (e.g. Sat A-B and Sat B-A) across different candidate groups, allowing potential cross-partition leakage. | High | **FIXED** | Implemented canonical pair tracking `(min(id1, id2), max(id1, id2))` in `ml/build_dataset.py` and added `canonical_pair_id` to feature engineering. Rebuilt dataset: 177 unique pairs, 0 reverse pairs. |
| **AUD-06** | `ml/train_baseline.py` | Dynamic baseline threshold: physical baseline previously hardcoded 25 km threshold even when dataset was generated with higher proximity thresholds. | Medium | **FIXED** | Updated `train_baseline.py` to read `threshold_km` dynamically from dataset metadata JSON. |
| **AUD-07** | `models/artifacts` Sync | Specification required `models/artifacts/`, but training output was saving only to `ml/artifacts/`. | Low | **FIXED** | Updated `ml/train_baseline.py` to save to both locations simultaneously. Configured `backend/prediction_service.py` to transparently fall back between both paths. |
| **AUD-08** | Automated Test Coverage | Specification listed `test_dataset_pipeline.py`, `test_model_validation.py`, and `test_integration.py`, which were missing from the repo. | Medium | **FIXED** | Created `tests/test_dataset_pipeline.py`, `tests/test_model_validation.py`, and `tests/test_integration.py` (including Streamlit `AppTest` headless multi-page navigation and screening execution). All 48 tests pass. |
| **AUD-09** | Historical Data Ingestion | The repository contained current snapshots but no genuine multi-year historical archive. | Medium | **PARTIAL** | Preserved proxy task formulation honestly. Created `scripts/collect_snapshot.py` to enable periodic automated snapshot archival with provenance manifests. Documented single-snapshot limitation in model card. |
| **AUD-10** | Statistical Collision Probability ($P_c$) | Public TLEs lack covariance matrices. Operational $P_c$ cannot be computed. | Critical | **PASS** | Audited `backend/risk_assessment.py`. Confirmed $P_c$ is strictly gated as `unavailable` with honest educational explanation. Zero synthetic covariance matrices are manufactured. |
| **AUD-11** | Heuristic Risk Score Interpretation | Score is a project-defined heuristic (weights 70/15/15), not an aerospace safety standard. | High | **PASS** | Confirmed UI, reports, and code clearly label the score as a dimensionless ranking aid (0-100) and never describe it as a collision probability. |
| **AUD-12** | Live CelesTrak Connectivity | Live requests to `celestrak.org` could fail in offline environments. | Low | **PASS** | Verified that offline operation works using the bundled sample catalog (`sample_catalog.tle`), and unit tests mock HTTP calls completely. |

---

## 4. Verification Evidence & Summary

- **Unit & Integration Tests:** 48 passed in 8.13s (`pytest -v`).
- **Streamlit Headless AppTest:** 7/7 pages verified (`Mission overview`, `Satellite selection`, `Conjunction screening`, `Orbital visualization`, `Risk assessment`, `ML model evaluation`, `Data and system health`) with 0 unhandled exceptions.
- **Machine Learning Verification:**
  - Evaluated on $N = 36$ held-out candidate groups with 0 reverse-pair leakage.
  - ML F1: 0.651, ROC-AUC: 0.613, PR-AUC: 0.649, Brier Score: 0.249.
  - Physical baseline F1: 0.087; ML demonstrates measurable improvement over static $t_0$ separation on held-out candidate groups.
- **Operational Verdict:** **READY FOR DEMONSTRATION WITH DOCUMENTED SCIENTIFIC LIMITATIONS**.
