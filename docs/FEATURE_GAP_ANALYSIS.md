# OrbitalGuard AI ? Feature Gap Analysis & Improvement Plan

**Date:** October 14, 2026  
**Scope:** Evaluation of actual system capabilities vs research-oriented space situational awareness objectives.

---

## 1. Objective vs Real Capabilities Overview

The stated objective of **OrbitalGuard AI** is to provide an end-to-end research-grade space situational awareness system to:
1. Retrieve public orbital element data.
2. Propagate orbits with standard SGP4/SDP4 in the TEME frame.
3. Detect candidate geometric close approaches (conjunctions) over configurable forecast horizons.
4. Refine times of closest approach and minimum separation distances.
5. Provide transparent proximity risk ranking while strictly segregating uncomputed statistical collision probability.
6. Provide an honest, reproducible proxy machine learning pipeline.
7. Present all results in an interactive, responsive Streamlit dashboard.

---

## 2. Feature Gap Evaluation Matrix

| Feature / Capability | Problem Solved | Implementation Status | Feasibility & Safety | Affected Files | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Canonical Pair Deduplication** | Prevents reverse-ordered duplicate pairs (e.g. A-B and B-A) from inflating datasets and leaking across train/test splits. | **IMPLEMENTED** | High / Safe | `backend/feature_engineering.py`, `ml/build_dataset.py`, `ml/train_baseline.py` | Verified 0 reverse pairs in `proxy_dataset.csv` and zero leakage in `test_model_validation.py`. |
| **Candidate Search in Screening Table** | Enables users to quickly filter and isolate specific candidate satellites from large catalog runs without manual scrolling. | **IMPLEMENTED** | High / Safe | `frontend/pages/conjunction_screening.py` | Tested interactive text input filtering by candidate name and catalog ID. |
| **Historical Snapshot Collector** | Bridges the gap between current single snapshots and multi-epoch historical time-series datasets. | **IMPLEMENTED** | High / Safe | `scripts/collect_snapshot.py` | Verified live execution saving timestamped TLEs and SHA-256 manifests to `data/historical/`. |
| **Plotly Datetime Line Bug Fix** | Eliminates runtime crash when drawing closest-approach time markers on datetime axes in Plotly charts. | **IMPLEMENTED** | High / Safe | `frontend/visualizations.py` | Headless `AppTest` verified rendering without exceptions. |
| **Transparent Risk Breakdown in Reports** | Ensures exported text reports explicitly document the 70/15/15 heuristic weights and the reason for $P_c$ unavailability. | **IMPLEMENTED** | High / Safe | `backend/report_service.py` | Tested via `test_report_and_prediction.py` and `test_integration.py`. |
| **Multi-Directory Artifact Sync** | Ensures both `ml/artifacts/` and `models/artifacts/` remain synchronized so CLI tools and external scripts never find missing models. | **IMPLEMENTED** | High / Safe | `ml/train_baseline.py`, `backend/prediction_service.py` | Tested with `test_report_and_prediction.py`. |
| **Configurable Freshness Limits** | Informs users when orbital elements are stale relative to forecast horizons. | **IMPLEMENTED** | High / Safe | `backend/data_sources.py`, `frontend/components.py` | Tested in `test_data_sources.py` and displayed on Satellite Selection preview. |
| **Offline-Safe Bundled Catalog** | Allows complete end-to-end evaluation and demonstration in network-isolated or firewall environments. | **IMPLEMENTED** | High / Safe | `data/sample_metadata/sample_catalog.tle`, `frontend/pages/satellite_selection.py` | Verified with offline AppTest and offline unit tests. |
| **Covariance-Based Collision Probability ($P_c$)** | Physical calculation of encounter-plane collision probability using 3D covariance. | **GATED (UNAVAILABLE)** | Unsafe without real covariance | `backend/risk_assessment.py` | Unit tests verify status is `unavailable`. Manufacturing fake covariance is strictly rejected. |
| **Full Historical Time-Series ML** | Training temporal sequence models (e.g. LSTM/GNN) across multi-year historical conjunction records. | **FUTURE SCOPE** | Requires months of collected snapshots | `ml/`, `data/historical/` | Tooling provided via `scripts/collect_snapshot.py`. Single snapshot proxy formulation retained honestly. |
| **High-Fidelity Numerical Perturbations** | Integration of non-spherical gravity, atmospheric drag fluctuations, solar radiation pressure beyond SGP4 analytical theory. | **FUTURE SCOPE** | Requires numerical integrator (e.g., Orekit / Cowell) | `backend/orbital_propagation.py` | Documented as a fundamental analytical SGP4 limitation in `docs/limitations.md`. |

---

## 3. High-Value Enhancements Completed During Audit

1. **Reverse-Pair Elimination & Canonical Pair Tracking**:  
   - Added `canonical_pair_id` in `backend/feature_engineering.py`.
   - Updated `ml/build_dataset.py` with `seen_canonical_pairs` set tracking to ensure symmetric pairs $(A, B)$ and $(B, A)$ are not duplicated.
   - Updated `ml/train_baseline.py` to assert zero group leakage across canonical pair IDs.

2. **Snapshot Collector Workflow (`scripts/collect_snapshot.py`)**:  
   - Allows users to schedule or run cron jobs to accumulate periodic CelesTrak snapshots into `data/historical/`.
   - Writes timestamped files and SHA-256 manifests preserving data provenance.

3. **Candidate Search Filter in Dashboard**:  
   - Added text filter input in `frontend/pages/conjunction_screening.py` enabling real-time substring search by satellite name or catalog ID across screening results.

4. **Visualizer Robustness**:  
   - Resolved Plotly `add_vline` runtime bug by using `add_shape(type='line', yref='paper')` and `add_annotation` for TCA markers.

5. **Beginner-Friendly Guidance & Viva Preparation**:  
   - Created `docs/BEGINNER_GUIDE.md` covering all 15 required sections from foundational physics to viva questions.
