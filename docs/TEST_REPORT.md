# OrbitalGuard AI ? Test Execution and Verification Report

**Project**: OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine  
**Document**: `docs/TEST_REPORT.md`  
**Test Suite**: Pytest 8.3.4, Streamlit Testing Framework  
**Execution Timestamp**: October 28, 2026  
**Environment**: Windows 11, Python 3.13.5 (Anaconda), Intel x86_64  
**Test Root**: `E:\orbitalguard-ai`  

---

## 1. Test Summary

| Metric | Result |
|:---|:---:|
| **Total Tests Collected** | **54** |
| **Tests Passed** | **54** (100%) |
| **Tests Failed** | **0** |
| **Tests Skipped** | **0** |
| **Tests Blocked** | **0** |
| **Execution Duration** | **24.91 seconds** |
| **Exit Code** | `0 (Success)` |

---

## 2. Module Breakdown

### 2.1 TLE Parser Tests (`tests/test_tle_parser.py`) ? 10 Passed
- `test_valid_iss_tle_parses`: Verifies standard ISS ZARYA 2LE format checksum and fields.
- `test_invalid_checksum_rejected`: Confirms invalid modulo-10 checksum is flagged.
- `test_truncated_line_fails`: Confirms short/truncated lines raise validation errors.
- `test_catalog_id_mismatch_fails`: Ensures line 1 and line 2 NORAD IDs must match.
- `test_non_ascii_cleared`: Replaces non-printable or corrupt characters gracefully.
- `test_blank_line_handling`: Confirms blank/whitespace lines do not corrupt consecutive 2LE/3LE parsing.
- `test_catalog_duplicate_handling`: Detects and removes identical duplicate TLE records.
- `test_upload_size_limit_rejection`: Enforces the 2 MB maximum upload boundary.
- `test_extract_orbital_parameters`: Validates extraction of inclination, eccentricity, mean motion.
- `test_stale_element_age_calculation`: Validates accurate UTC epoch subtraction.

### 2.2 Orbital Propagation Tests (`tests/test_orbital_propagation.py`) ? 5 Passed
- `test_vanguard_sgp4_at_epoch`: Validates Vanguard 1 (sat 00005) against David Vallado's benchmark `tcppver.out` reference coordinates.
- `test_space_track_sat88888_benchmark`: Validates synthetic benchmark sat 88888 against Space-Track Report No. 3 reference ephemeris ($x = 2328.97\text{ km}$, $y = -5995.22\text{ km}$, $z = 1719.97\text{ km}$).
- `test_teme_coordinate_units`: Verifies position is strictly kilometres and velocity is kilometres/second.
- `test_sgp4_error_code_handling`: Ensures non-zero SGP4 numerical error codes (e.g. decayed orbit, eccentric element error) raise `PropagationError`.
- `test_propagate_many_monotonic_time`: Confirms vectorized propagation produces strictly monotonic time series.

### 2.3 Coordinate Utilities Tests (`tests/test_coordinate_utils.py`) ? 5 Passed
- `test_relative_position_euclidean`: Confirms $\Delta\vec{r} = \vec{r}_2 - \vec{r}_1$.
- `test_relative_velocity_euclidean`: Confirms $\Delta\vec{v} = \vec{v}_2 - \vec{v}_1$.
- `test_miss_distance_scalar`: Confirms $\|\Delta\vec{r}\|$ calculation.
- `test_relative_speed_scalar`: Confirms $\|\Delta\vec{v}\|$ calculation.
- `test_spherical_altitude_km`: Confirms altitude relative to WGS-84 equatorial radius ($6378.137\text{ km}$).

### 2.4 Conjunction Screening Tests (`tests/test_conjunction_screening.py`) ? 3 Passed
- `test_screening_detects_close_approach`: Validates coarse uniform grid evaluation and boundary handling.
- `test_numerical_refinement_brent`: Validates SciPy bounded 1D optimization for finding refined Time of Closest Approach (TCA) and minimum separation.
- `test_candidate_filtering_and_sorting`: Verifies closest candidate approaches are ranked correctly by miss distance.

### 2.5 Risk Assessment Tests (`tests/test_risk_assessment.py`) ? 3 Passed
- `test_heuristic_scoring_formula`: Validates exact 70/15/15 weighting:
  $$\text{Score} = 100 \times \left( 0.70 \cdot \text{sep\_term} + 0.15 \cdot \text{vel\_term} + 0.15 \cdot \text{fresh\_term} \right)$$
- `test_collision_probability_gate`: **Strict Verification**: Confirms $P_c$ remains `None` with status `"unavailable"` when error covariance is absent.
- `test_plain_language_explanation`: Validates transparent explanation string generation.

### 2.6 Data Sources & CelesTrak HTTP Tests (`tests/test_data_sources.py`) ? 10 Passed
- `test_fetch_group_parses_and_caches`: Mocks 200 OK GP response; confirms parsing and caching into `data/cache` and `data/raw`.
- `test_missing_catalog_id`: Confirms `ObjectNotFoundError` when CelesTrak returns "No GP data found".
- `test_rate_limit`: Confirms HTTP 429 triggers `RateLimitedError` after bounded backoff.
- `test_freshness_warnings_for_old_elements`: Confirms stale element age warnings.
- `test_permanent_http_error`: Confirms HTTP 404 raises `DataSourceError` without useless retrying.
- `test_connect_timeout_handling`: **New**: Confirms connection timeouts raise `DataSourceError` with diagnostic instructions.
- `test_read_timeout_handling`: **New**: Confirms socket read timeouts raise `DataSourceError`.
- `test_dns_failure_handling`: **New**: Confirms DNS lookup failures raise `DataSourceError("DNS lookup failed...")`.
- `test_user_agent_header_set`: **New**: Verifies `User-Agent: OrbitalGuardAI/0.1.0` is configured on all outbound requests.
- `test_find_and_load_offline_snapshot`: **New**: Validates offline snapshot discovery in `data/cache` and `data/raw` and offline loading.

### 2.7 Dataset Pipeline & Feature Engineering Tests ? 3 Passed
- `tests/test_dataset_pipeline.py`:
  - `test_build_dataset_deduplication`: Confirms canonical pair deduplication $\min(\text{id}_1, \text{id}_2), \max(\text{id}_1, \text{id}_2)$ eliminates reverse-pair leakage.
  - `test_target_label_definition`: Confirms `below_threshold_proxy` is derived from refined propagation.
- `tests/test_feature_engineering.py`:
  - `test_feature_schema_consistency`: Validates feature ordering and presence of 18 orbital and relative features.

### 2.8 ML Model Validation Tests ? 7 Passed
- `tests/test_ml_validation.py`:
  - `test_no_label_leakage_in_features`: Confirms features do not contain future refined miss distance or label transformations.
  - `test_grouped_chronological_split`: Confirms grouping by candidate and canonical pair prevents partition leakage.
- `tests/test_model_validation.py`:
  - `test_model_artifact_loadable`: Loads `baseline_model.joblib` and validates scikit-learn pipeline integrity.
  - `test_model_metadata_consistency`: Verifies `baseline_model.meta.json` schema and metrics.
  - `test_feature_ordering_match`: Verifies training feature names match prediction schema.
  - `test_prediction_output_schema`: Verifies `ml_proxy_score` (probability) and `ml_proxy_label` (binary).
  - `test_improves_physical_baseline`: Confirms ML proxy outperforms naive epoch baseline on F1 score.

### 2.9 Reporting & Prediction Service Tests (`tests/test_report_and_prediction.py`) ? 4 Passed
- `test_export_csv`: Validates CSV export structure and column headers.
- `test_export_text`: Validates plaintext report generation including 70/15/15 breakdown and $P_c$ gating explanation.
- `test_prediction_service_fallback`: Confirms safe fallback when artifact is missing.
- `test_report_contains_provenance`: Confirms SHA-256 and source URLs appear in exported text reports.

### 2.10 End-to-End Integration & Headless UI Tests (`tests/test_integration.py`) ? 4 Passed
- `test_end_to_end_conjunction_workflow`: Executes full pipeline (Parse -> Propagate -> Screen -> Risk -> ML -> Report).
- `test_all_frontend_pages_renderable`: Verifies all 7 page render functions execute without backend exceptions.
- `test_streamlit_app_ui_navigation_and_screening`: Uses Streamlit `AppTest` to simulate user clicking through all 7 pages, loading bundled sample, and starting screening.
- `test_satellite_selection_fallback_on_network_failure`: **New**: Simulates CelesTrak timeout and verifies fallback container and buttons appear.

---

## 3. What Passing Tests Prove & What They Do Not Prove

> [!IMPORTANT]
> - **What Passing Tests Prove**:
>   1. The software codebase is free of syntax errors, broken imports, missing dependencies, and runtime exceptions.
>   2. The numerical implementations of SGP4, TEME coordinates, and miss distance match published reference values (Vallado benchmarks).
>   3. The ML pipeline handles data without reverse-pair leakage and produces reproducible predictions from verified artifacts.
>   4. Streamlit UI navigation and session state management function across all 7 pages.
> - **What Passing Tests Do NOT Prove**:
>   1. Passing software tests do NOT prove that an orbital close approach will result in a physical collision.
>   2. Passing tests do NOT validate real-world operational collision avoidance, which requires calibrated error covariance matrices from the 18th Space Defense Squadron (18 SDS).
>   3. High ML proxy accuracy indicates ability to approximate SGP4 geometric thresholding from orbital state features, NOT real-world collision prediction.
