# OrbitalGuard AI ? Feature Status and Implementation Matrix

**Project**: OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine  
**Document**: `docs/FEATURE_STATUS.md`  
**Status Date**: October 2026  
**Overall Project Status**: **READY FOR DEMONSTRATION & RESEARCH EVALUATION**  

---

## 1. Feature Implementation Matrix

| Category | Feature Name | Description | Status | Evidence & Test Location |
|:---|:---|:---|:---:|:---|
| **Data Ingestion** | Live CelesTrak GP Ingestion | Fetches live GP TLE records from CelesTrak endpoint | **VERIFIED** | `backend/data_sources.py`, `tests/test_data_sources.py` |
| **Data Ingestion** | Resilient Request Handling | User-Agent identification, split connect/read timeouts (6s/20s), bounded retries | **VERIFIED** | `test_connect_timeout_handling`, `test_read_timeout_handling` |
| **Data Ingestion** | Offline Disk Snapshot Fallback | Automatically discovers cached/raw snapshots on disk when cloud IPs are rate-limited | **VERIFIED** | `find_offline_snapshot`, `test_find_and_load_offline_snapshot` |
| **Data Ingestion** | Bundled Offline Sample | 4 verified historical objects (ISS, NOAA 15, Iridium, Cosmos) for 100% offline use | **VERIFIED** | `data/sample_metadata/sample_catalog.tle` |
| **Data Ingestion** | TLE / 3LE File Upload | Uploads custom catalogs with 2 MB safety ceiling and line checksum validation | **VERIFIED** | `tests/test_tle_parser.py::test_upload_size_limit_rejection` |
| **Data Ingestion** | Search by Name / Catalog ID | Individual object lookup from CelesTrak or loaded session catalogs | **VERIFIED** | `test_missing_catalog_id`, `satellite_selection.py` |
| **Astrodynamics** | SGP4 Propagation Engine | Analytical Brouwer-Lyddane propagator producing Cartesian states in TEME frame | **VERIFIED** | Grounded in Vallado `tcppver.out` sat 00005 & sat 88888 |
| **Astrodynamics** | Coordinate Consistency | Strictly kilometres ($\text{km}$), km/s ($\text{km/s}$), and UTC timestamps | **VERIFIED** | `tests/test_coordinate_utils.py` (5 passed) |
| **Astrodynamics** | SGP4 Error Trapping | Rejects decayed or unphysical orbits cleanly via `PropagationError` | **VERIFIED** | `tests/test_orbital_propagation.py::test_sgp4_error_code_handling` |
| **Screening** | Two-Stage Conjunction Screen | Coarse uniform time sampling with candidate boundary pruning | **VERIFIED** | `tests/test_conjunction_screening.py` (3 passed) |
| **Screening** | Numerical Refinement | SciPy Brent scalar optimization over local separation minima to find exact TCA | **VERIFIED** | `ConjunctionScreeningService._refine_approach` |
| **Screening** | Interactive Table & Filtering | Filter by candidate name, catalog ID, miss distance slider, within-threshold flag | **VERIFIED** | `frontend/pages/conjunction_screening.py` |
| **Visualization** | 3D Interactive TEME Viewer | WebGL 3D orbit render with reference Earth sphere, trajectory splines, time slider | **VERIFIED** | `frontend/pages/orbital_visualization.py` |
| **Visualization** | Time-Series Encounter Plots | Plotly charts of separation distance (km) and relative speed (km/s) vs time | **VERIFIED** | Replaced `add_vline` with `add_shape` to prevent datetime bug |
| **Risk Analysis** | Geometric Proximity Metrics | Precise miss distance, TCA timestamp, relative velocity vector | **VERIFIED** | `tests/test_risk_assessment.py` |
| **Risk Analysis** | Heuristic Screening Score | 0 to 100 transparent score: 70% separation, 15% relative speed, 15% element freshness | **VERIFIED** | `tests/test_risk_assessment.py::test_heuristic_scoring_formula` |
| **Risk Analysis** | Collision Probability ($P_c$) Gating | **Strict Scientific Rule**: $P_c$ remains `unavailable` due to lack of covariance in TLEs | **VERIFIED** | `test_collision_probability_gate` |
| **Machine Learning** | ML Proxy Target Definition | Predicts `below_threshold_proxy` (refined SGP4 miss distance $\le$ threshold) | **VERIFIED** | `ml/build_dataset.py`, `docs/model_card.md` |
| **Machine Learning** | Data Leakage Prevention | Canonical pair deduplication $\min(\text{id}_1, \text{id}_2), \max(\text{id}_1, \text{id}_2)$ prevents reverse pairs | **VERIFIED** | `tests/test_dataset_pipeline.py::test_build_dataset_deduplication` |
| **Machine Learning** | Chronological Grouped Split | Grouped by candidate ID and canonical pair across chronological partitions | **VERIFIED** | `tests/test_ml_validation.py::test_grouped_chronological_split` |
| **Machine Learning** | Model Pipeline & Artifacts | SimpleImputer -> StandardScaler -> LogisticRegression saved with SHA-256 metadata | **VERIFIED** | `models/artifacts/baseline_model.joblib` |
| **Machine Learning** | Reproducible Evaluation | Evaluated on held-out test set ($N=36$): Accuracy 58.3%, F1 0.651 vs physical 0.087 | **VERIFIED** | `ml/evaluate_model.py`, `docs/model_card.md` |
| **Reporting** | CSV Encounter Export | Exports tabular encounter geometry with provenance and parameters | **VERIFIED** | `tests/test_report_and_prediction.py::test_export_csv` |
| **Reporting** | Plaintext Encounter Summary | Exports comprehensive human-readable report with 70/15/15 weights and $P_c$ gating | **VERIFIED** | `tests/test_report_and_prediction.py::test_export_text` |
| **System Health** | Cache & Provenance Inspector | Lists cached `.tle` files with age, TTL status, and SHA-256 digests | **VERIFIED** | `frontend/pages/system_health.py` |
| **Historical Archive** | Periodic Snapshot Collector | CLI workflow to collect timestamped catalogs with SHA-256 manifests | **VERIFIED** | `scripts/collect_snapshot.py` |
| **Testing** | Automated Pytest Suite | 54 unit, integration, benchmark, and UI tests | **VERIFIED** | 54 passed in 24.91s |
| **Testing** | Streamlit AppTest UI Suite | Simulates headless browser user interaction across all 7 pages | **VERIFIED** | `tests/test_integration.py` |

---

## 2. Capabilities Explicitly NOT Claimed (Scientific Honesty Disclosures)

1. **Certified Operational Collision Avoidance**: This application is an educational and research prototype. It must not be used for satellite maneuver execution without primary radar tracking from the 18th Space Defense Squadron (18 SDS).
2. **Real Collision Outcomes**: The ML model predicts a geometric proximity proxy label (`below_threshold_proxy`), NOT physical collision outcomes or catastrophic breakup events.
3. **Maneuver Prediction**: Propagation assumes ballistic orbital motion under gravitational and drag perturbations; it cannot anticipate station-keeping or avoidance burns.
4. **Statistical Covariance ($P_c$)**: Genuine collision probability calculations are disabled because public two-line element sets do not publish error covariance matrices.
