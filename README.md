# OrbitalGuard AI - Space Debris Proximity Forecasting and Collision Risk Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-48%20Passed-brightgreen.svg)]()
[![Propagator](https://img.shields.io/badge/Propagator-SGP4%20TEME-informational.svg)]()
[![Framework](https://img.shields.io/badge/UI-Streamlit-red.svg)]()

Research prototype space situational awareness application for relative orbital geometry forecasting, conjunction screening, proximity risk prioritization, and defensible proxy machine-learning evaluation using public NORAD General Perturbations (GP) Two-Line Element (TLE) records.

> **CRITICAL SCIENTIFIC & SAFETY NOTICE**  
> OrbitalGuard AI is an academic and research engineering prototype. It is **not** a certified operational collision-avoidance system.  
> 1. A predicted geometric close approach is **not** an actual collision.  
> 2. Public TLE records do not contain state covariance matrices; therefore, **statistical collision probability ($P_c$) is physically unavailable and is explicitly gated as such**. Arbitrary covariance matrices are never manufactured.  
> 3. Heuristic screening scores (0-100) are interpretable geometric ranking aids, not physical probabilities or aerospace safety standards.  
> 4. Machine learning models predict a proxy geometric label (`below_threshold_proxy`) and do not predict physical collision events.

---

## Complete Project Documentation

| Document | Purpose |
| :--- | :--- |
| **[Beginner's Technical Guide](docs/BEGINNER_GUIDE.md)** | **Exhaustive 15-section guide covering physics, math, architecture, and 35 viva questions.** |
| **[Project Audit Report](docs/PROJECT_AUDIT_REPORT.md)** | Comprehensive audit findings, bug fixes, evidence matrix, and status categories. |
| **[Feature Gap Analysis](docs/FEATURE_GAP_ANALYSIS.md)** | Real capabilities vs objective, gap analysis, and implemented improvements. |
| **[Verification Results](docs/VERIFICATION_RESULTS.md)** | Independent test run logs, environment details, and verified metrics. |
| **[Architecture Guide](docs/architecture.md)** | System components, module structure, and data flow diagrams. |
| **[Model Card](docs/model_card.md)** | ML model architecture, features, grouped holdout split, and test metrics. |
| **[Research Notes](docs/research_notes.md)** | SGP4 theory, TEME coordinate frames, and covariance requirements. |
| **[Data Dictionary](docs/data_dictionary.md)** | Complete definitions, units (km, km/s, UTC), and field constraints. |
| **[Scientific Limitations](docs/limitations.md)** | Plain-language operational and analytical limitations. |
| **[Implementation Status](docs/IMPLEMENTATION_STATUS.md)** | Current feature completion status and verification matrix. |

---

## Architecture & Scientific Workflow

```
Public CelesTrak GP / User TLE / Bundled Sample
                     ?
                     ?
          [TLEValidationService]
       (Line structure, checksums, epoch)
                     ?
                     ?
           [DataSourceService]
     (HTTP retries, TTL cache, manifests)
                     ?
                     ?
       [OrbitalPropagationService]
       (Standard SGP4, TEME frame)
                     ?
                     ?
      [ConjunctionScreeningService]
   (Coarse filtering, local minima search,
     bounded Golden-Section TCA refinement)
                     ?
                     ?
           [RiskAssessmentService]
   ??? 1. Geometric Proximity (TCA, miss distance, relative velocity)
   ??? 2. Transparent Heuristic Ranking Score (0 to 100)
   ??? 3. Statistical Collision Probability Gate (Pc unavailable without covariance)
                     ?
                     ?
       [FeatureEngineeringService]
    (Derived relative orbital kinematics at t0)
                     ?
                     ?
        [ModelPredictionService]
    (Trusted local pipeline: Imputer -> Scaler -> LogisticRegression)
                     ?
                     ?
          [Interactive Streamlit UI]
  (7 dedicated pages with Plotly 3D visualizer, CSV & TXT report export)
```

---

## Windows Setup & Execution (PowerShell)

Follow these exact steps from the project root (`C:\Users\DELL\orbitalguard-ai`):

### 1. Open PowerShell in Project Root
```powershell
cd C:\Users\DELL\orbitalguard-ai
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Required Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Preflight Diagnostics
Verifies environment, imports, package versions, and required directory structure:
```powershell
python scripts\run_preflight.py
```

### 5. Execute Automated Test Suite
Runs all 48 unit, orbital mechanics, risk assessment, ML validation, and UI integration tests:
```powershell
pytest -v
```

### 6. Launch the Streamlit Dashboard
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Optional CLI Workflows

### Download Current Catalog Snapshots
Fetches real CelesTrak GP orbital elements with SHA-256 caching and manifest provenance:
```powershell
# Download weather satellites
python scripts\download_catalog.py --group weather

# Download visual satellites
python scripts\download_catalog.py --group visual

# Download active satellites
python scripts\download_catalog.py --group active
```

### Collect Historical Snapshots for Long-Term Archival
```powershell
python scripts\collect_snapshot.py --groups stations visual
```

### Build Proxy ML Dataset
Constructs a leakage-resistant dataset with deduplicated canonical pairs:
```powershell
python -m ml.build_dataset --horizon-hours 12 --threshold-km 3000 --sample-seconds 120 --max-candidates 60
```

### Train and Evaluate Baseline Model
Trains a reproducible scikit-learn pipeline with grouped chronological holdout validation:
```powershell
python -m ml.train_baseline
```

### Score External Features with Prediction Service
```powershell
python -m ml.predict data\processed\proxy_dataset.csv
```

---

## Streamlit Application Pages

1. **Mission Overview**: Executive summary with target metadata, screening settings, detected candidates, minimum miss distance, and propagation statistics.
2. **Satellite Selection**: Search CelesTrak by satellite name, NORAD catalog ID, catalog group, or upload custom TLE files. Includes an offline-safe bundled sample catalog (ISS, NOAA 15, Envisat, Vanguard 1).
3. **Conjunction Screening**: Configurable forecast horizons (6, 12, 24, 48, 72 hours), geometric thresholds (0.1-5000 km), and uniform sampling intervals. Displays real-time candidate search filter, sortable results, candidate selector, miss distance distribution, and relative trajectory series.
4. **Orbital Visualization**: Plotly 3D visualization in TEME frame showing Earth scale sphere, target trajectory, candidate trajectory, and closest approach encounter point.
5. **Risk Assessment**: Strict separation of Geometric Proximity, Heuristic Ranking Score (0-100 with transparent weights), and Statistical Collision Probability ($P_c$).
6. **ML Model Evaluation**: Displays trained model type, target definition, feature coefficients, grouped test metrics (PR-AUC, ROC-AUC, Brier score, Confusion matrix), baseline comparisons, and honest limitation disclosures.
7. **Data and System Health**: Diagnostics panel reporting cache hits, element freshness, propagation errors, log viewer, and CSV/text report exports.

---

## Test Suite Overview (`tests/`)

| Test File | Focus |
| :--- | :--- |
| `test_tle_parser.py` | Line layout, checksum modulo-10 validation, epoch parsing, deduplication, corrupt input rejection. |
| `test_orbital_propagation.py` | SGP4 propagation against Vallado sat 5 benchmark (`tcppver.out`) and Space-Track Report No. 3 benchmark sat 88888. |
| `test_coordinate_utils.py` | TEME relative vector math, spherical altitudes, Julian date conversions, frame consistency guards. |
| `test_conjunction_screening.py` | Coarse-grid screening, local minima isolation, Golden-Section numerical TCA refinement, batch propagation. |
| `test_risk_assessment.py` | Heuristic score bounds (0..100), boundary conditions, Pc gate enforcement without covariance. |
| `test_feature_engineering.py` | Feature extraction from relative kinematics, unit consistency, schema preservation. |
| `test_dataset_pipeline.py` | Snapshot loading, dataset synthesis, feature schema verification, proxy label bounds. |
| `test_model_validation.py` | Grouped chronological splitting, prevention of candidate ID leakage, metric computations, origin verification. |
| `test_data_sources.py` | CelesTrak client, transient retry backoff, SHA-256 disk cache, upload parsing, mocked offline requests. |
| `test_report_and_prediction.py` | CSV and TXT report generation, model prediction service lifecycle. |
| `test_integration.py` | Full end-to-end workflow and headless Streamlit `AppTest` multi-page navigation and screening execution. |
