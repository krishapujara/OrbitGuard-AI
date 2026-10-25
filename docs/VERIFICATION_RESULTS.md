# OrbitalGuard AI ? Independent Verification & Validation Results

**Verification Date:** October 14, 2026  
**Auditor:** Autonomous Verification & Testing Engine  
**Operating System:** Windows 11 (AMD64)  
**Python Runtime:** Python 3.13.5 (packaged by Anaconda, Inc.)  
**Test Framework:** Pytest 8.3.4  
**Primary UI Engine:** Streamlit 1.45.1  
**Orbital Mechanics Engine:** SGP4 2.27  

---

## 1. Automated Test Suite Execution

Command executed:
```powershell
pytest -v
```

### Direct Test Results by Module:
```
tests/test_conjunction_screening.py::test_local_minima PASSED                         [ 2%]
tests/test_conjunction_screening.py::test_screen_sample_catalog PASSED                 [ 4%]
tests/test_conjunction_screening.py::test_invalid_horizon_rejected PASSED             [ 6%]
tests/test_coordinate_utils.py::test_vector_conversion_and_finite_guard PASSED       [ 8%]
tests/test_coordinate_utils.py::test_relative_vectors_and_metrics PASSED             [10%]
tests/test_coordinate_utils.py::test_spherical_altitude PASSED                        [12%]
tests/test_coordinate_utils.py::test_julian_roundtrip PASSED                         [14%]
tests/test_coordinate_utils.py::test_frame_guard PASSED                               [16%]
tests/test_data_sources.py::test_fresh_download_and_cache PASSED                       [18%]
tests/test_data_sources.py::test_retry_transient_error PASSED                          [20%]
tests/test_data_sources.py::test_permanent_error_no_retry PASSED                       [22%]
tests/test_data_sources.py::test_parse_upload_valid_and_empty PASSED                   [25%]
tests/test_data_sources.py::test_freshness_warnings PASSED                             [27%]
tests/test_dataset_pipeline.py::test_load_snapshot_parses_sample_catalog PASSED       [29%]
tests/test_dataset_pipeline.py::test_build_dataset_creates_dataset_and_metadata PASSED [31%]
tests/test_feature_engineering.py::test_feature_vector_shape_and_types PASSED         [33%]
tests/test_integration.py::test_end_to_end_conjunction_workflow PASSED               [35%]
tests/test_integration.py::test_all_frontend_pages_renderable PASSED                 [37%]
tests/test_integration.py::test_streamlit_app_ui_navigation_and_screening PASSED    [39%]
tests/test_ml_validation.py::test_grouped_split_holds_out_candidates PASSED          [41%]
tests/test_ml_validation.py::test_split_rejects_too_few_groups PASSED                 [43%]
tests/test_model_validation.py::test_grouped_split_holds_out_candidates PASSED       [45%]
tests/test_model_validation.py::test_split_rejects_too_few_groups PASSED              [47%]
tests/test_model_validation.py::test_classification_report_metrics PASSED            [50%]
tests/test_model_validation.py::test_majority_baseline_predicts_most_frequent PASSED  [52%]
tests/test_model_validation.py::test_prediction_service_rejects_untrusted_origin PASSED [54%]
tests/test_orbital_propagation.py::test_vanguard_sgp4_at_epoch PASSED                  [56%]
tests/test_orbital_propagation.py::test_benchmark_88888_sgp4_at_epoch PASSED         [58%]
tests/test_orbital_propagation.py::test_iss_propagation_finite PASSED                 [60%]
tests/test_orbital_propagation.py::test_propagate_many_skips_nothing_at_valid_times PASSED [62%]
tests/test_orbital_propagation.py::test_sample_interval_requires_positive_step PASSED [64%]
tests/test_report_and_prediction.py::test_report_export PASSED                        [66%]
tests/test_report_and_prediction.py::test_prediction_service_missing_artifact PASSED  [68%]
tests/test_report_and_prediction.py::test_dashboard_pages_registered PASSED           [70%]
tests/test_report_and_prediction.py::test_orbit_figure_teme_labels PASSED            [72%]
tests/test_risk_assessment.py::test_heuristic_score_bounds PASSED                     [75%]
tests/test_risk_assessment.py::test_heuristic_weight_breakdown PASSED                 [77%]
tests/test_risk_assessment.py::test_collision_probability_gate PASSED                 [79%]
tests/test_tle_parser.py::test_checksum_matches_published_digits PASSED              [81%]
tests/test_tle_parser.py::test_parse_sample_catalog PASSED                            [83%]
tests/test_tle_parser.py::test_catalog_identifier_mismatch PASSED                     [85%]
tests/test_tle_parser.py::test_checksum_mismatch_strict PASSED                        [87%]
tests/test_tle_parser.py::test_checksum_mismatch_non_strict_warns PASSED              [89%]
tests/test_tle_parser.py::test_incomplete_and_malformed_text PASSED                   [91%]
tests/test_tle_parser.py::test_duplicate_catalog_keeps_last PASSED                    [93%]
tests/test_tle_parser.py::test_epoch_conversion_iss PASSED                            [95%]
tests/test_tle_parser.py::test_epoch_conversion_vanguard PASSED                       [97%]
tests/test_tle_parser.py::test_records_by_query PASSED                                [100%]

============================= 48 passed in 12.87s =============================
```

---

## 2. Headless Streamlit UI Workflow Verification

Verified via `streamlit.testing.v1.AppTest`:
- Application initialized with space-inspired theme (`#070b14`).
- Page 1 (`Mission overview`): Metrics cards render real telemetry without errors.
- Page 2 (`Satellite selection`): Clicked "Load bundled sample (offline)". Loaded 4 records (`ISS`, `NOAA 15`, `ENVISAT`, `VANGUARD 1`). Target selected.
- Page 3 (`Conjunction screening`): Initiated SGP4 screening over 6h horizon with 25 km threshold. Screened 3 candidate objects, numerical TCA refinement converged, sortable dataframe rendered.
- Page 4 (`Orbital visualization`): Plotly 3D TEME Earth and orbital trajectory chart generated without exceptions.
- Page 5 (`Risk assessment`): Rendered geometric parameters, heuristic score (0-100), and verified that Collision Probability is explicitly displayed as UNAVAILABLE.
- Page 6 (`ML model evaluation`): Verified loading of trusted local artifact (`baseline_model.joblib`), displaying confusion matrix, ROC-AUC, PR-AUC, and feature coefficients.
- Page 7 (`Data and system health`): Verified diagnostics and report download buttons.
- Result: **0 Unhandled UI Exceptions**.

---

## 3. Machine Learning Model Re-Evaluation Verification

- **Evaluation Dataset:** Clean deduplicated dataset `proxy_dataset.csv` (177 unique pairs, 0 reverse pairs, 60 candidate groups).
- **Partitioning:** Chronological grouped holdout (60% Train, 20% Val, 20% Test) grouped by `candidate_id` and verified across `canonical_pair_id`.
- **Target Variable:** `below_threshold_proxy` (1 if refined SGP4 miss distance $\le 3000	ext{ km}$, 0 otherwise).
- **Test Set Size:** $N = 36$ held-out pairs.
- **Reproduced Metrics:**
  - Accuracy: $58.33\%$ (Baseline: $41.67\%$)
  - Precision: $63.64\%$ (Baseline: $50.00\%$)
  - Recall: $66.67\%$ (Baseline: $4.76\%$)
  - F1-Score: **$0.651$** (Physical Baseline: **$0.087$**)
  - PR-AUC: **$0.649$**
  - ROC-AUC: **$0.613$**
  - Brier Score: **$0.249$**
  - Log Loss: **$0.739$**
- **Artifact Paths:** Synchronized across `ml/artifacts/` and `models/artifacts/`.

---

## 4. What Was Verified vs What Was Not Verified

### A. Fully Verified (Proven with Execution Logs):
1. Complete Python preflight check passed.
2. 48 automated tests passed without failure.
3. SGP4 propagation matching official Vallado benchmark data.
4. Parsing of TLE sets with blank lines.
5. Live network query to CelesTrak (`visual` and `stations` groups).
6. SHA-256 disk caching and JSON manifest generation.
7. Offline operation using bundled sample catalog.
8. Interactive Streamlit AppTest multi-page navigation.
9. Elimination of reverse-pair data leakage in ML pipeline.
10. Gating of collision probability ($P_c$) as unavailable.

### B. What Was NOT Verified (Explicit Constraints):
1. **Multi-Year Historical Retrospective Conjunction Forecasting:** Verified only that the current catalog snapshot pipeline functions on a single day's data. Multi-year retrospective testing was NOT performed because public archives were not pre-downloaded for historical years.
2. **Real Physical Spacecraft Collision Validation:** Verified only the geometric proxy task (`below_threshold_proxy`). Real on-orbit collision events were NOT verified because public TLE catalogs do not contain labeled real collision outcomes.
3. **High-Fidelity Numerical Perturbations:** Cowell-integrator force models (JGM-3, solar radiation pressure, NRLMSISE-00 atmospheric density) were NOT verified because the project scope is specifically bounded to NORAD General Perturbations (SGP4) in TEME.
