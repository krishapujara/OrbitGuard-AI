# OrbitalGuard AI ? Deployed UI Test Matrix & Functional Audit

**Project**: OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine  
**Document**: `docs/DEPLOYED_UI_TEST_MATRIX.md`  
**Deployment Target**: `https://orbitguardai.streamlit.app/`  
**Local Testbed**: `http://localhost:8501`  
**Execution Environment**: Python 3.13.5, Streamlit 1.45.1, Chromium headless (`AppTest`)  

---

## 1. Multi-Page Interactive Audit

| Page Name | Interactive Control | Expected Behavior | Local Status | Cloud Status | Verification Method |
|:---|:---|:---|:---:|:---:|:---|
| **Mission Overview** | Metric cards | Reflect current target and screening statistics | **PASS** | **PASS** | `AppTest.metric` checks |
| **Mission Overview** | Failed objects expander | Displays SGP4 propagation failures table if failures > 0 | **PASS** | **PASS** | Evaluated on degraded TLE records |
| **Satellite Selection** | Catalog group selectbox | Select from 16 verified CelesTrak groups | **PASS** | **PASS** | Selectbox selection tested |
| **Satellite Selection** | **Load catalog group** | Loads satellites from live API or bundled snapshot | **PASS** | **PASS** | Verified on `stations`, `science`, `visual` |
| **Satellite Selection** | Refresh data button | Bypasses local cache to query live CelesTrak | **PASS** | **PASS** | Cache bypass verified |
| **Satellite Selection** | Search by name | Searches CelesTrak by satellite name string | **PASS** | **PASS** | Verified on "ISS" and "NOAA" |
| **Satellite Selection** | Search by catalog ID | Searches CelesTrak by 5-digit NORAD ID | **PASS** | **PASS** | Verified on "25544" and "20580" |
| **Satellite Selection** | Load bundled sample | Loads 4-object historical demonstration sample | **PASS** | **PASS** | Verified offline execution |
| **Satellite Selection** | TLE file uploader | Parses and validates custom 2LE/3LE files (2MB limit) | **PASS** | **PASS** | Verified valid and malformed files |
| **Satellite Selection** | Target selectbox | Selects primary satellite for conjunction screening | **PASS** | **PASS** | Session state persistence verified |
| **Conjunction Screening**| Forecast horizon selectbox | Configures propagation time (6h, 12h, 24h, 48h, 72h) | **PASS** | **PASS** | Horizon passed to SGP4 service |
| **Conjunction Screening**| Threshold number input | Configures geometric miss distance threshold (km) | **PASS** | **PASS** | Bounded [0.1, 5000.0] km |
| **Conjunction Screening**| Sampling interval slider | Uniform coarse time grid step (30s to 600s) | **PASS** | **PASS** | Bounded [30, 600] seconds |
| **Conjunction Screening**| Maximum candidates slider| Limits evaluated candidates for performance | **PASS** | **PASS** | Bounded [10, 400] candidates |
| **Conjunction Screening**| **Start screening** | Executes coarse SGP4 screen + Brent numerical refinement| **PASS** | **PASS** | Verified sub-second TCA and miss distance |
| **Conjunction Screening**| Candidate search input | Substring filter on candidate names and catalog IDs | **PASS** | **PASS** | `autocomplete="off"` verified |
| **Conjunction Screening**| Within-threshold checkbox | Toggles display of threshold-exceeding close approaches| **PASS** | **PASS** | Dynamic table filtering verified |
| **Conjunction Screening**| Separation & Speed plots | Time-series curves of miss distance and relative speed| **PASS** | **PASS** | Plotly cross-version shape render |
| **Orbital Visualization** | Candidate trajectory selectbox| Chooses secondary orbit to render in 3D scene | **PASS** | **PASS** | Selectbox selection tested |
| **Orbital Visualization** | Trajectory samples slider | Configures spline point density (20 to 180 points) | **PASS** | **PASS** | Resolution adjusted dynamically |
| **Orbital Visualization** | Time index slider | Steps forward and backward along propagated trajectory | **PASS** | **PASS** | Updates satellite marker position |
| **Orbital Visualization** | 3D WebGL Orbit Scene | Interactive 3D visualization in TEME celestial frame | **PASS** | **PASS** | Verified inertial Earth reference sphere |
| **Risk Assessment** | Geometric proximity metrics | Displays miss distance, TCA, relative velocity vector | **PASS** | **PASS** | Units strictly km and km/s |
| **Risk Assessment** | Heuristic screening score | Displays 0-100 score using 70/15/15 weighted formula | **PASS** | **PASS** | Explicitly marked `not_a_probability` |
| **Risk Assessment** | Statistical Pc gate | Displays `unavailable` due to lack of covariance in TLEs| **PASS** | **PASS** | **Strict Rule**: Zero manufactured data |
| **Risk Assessment** | ML proxy score card | Displays `below_threshold_proxy` score if model loaded | **PASS** | **PASS** | Scikit-learn inference pipeline |
| **ML Model Evaluation** | 3-Way baseline comparison | Compares ML model vs physical baseline vs dummy | **PASS** | **PASS** | Evaluated on held-out test set ($N=36$) |
| **ML Model Evaluation** | Confusion matrix heatmap | Interactive Plotly heatmap of true/false positive/neg | **PASS** | **PASS** | Verified counts |
| **ML Model Evaluation** | Feature coefficients bar | Interactive Plotly bar chart of model weights | **PASS** | **PASS** | 18 scaled features |
| **Data & System Health**| Diagnostics refresh | Re-runs health checks and updates timestamp | **PASS** | **PASS** | Responsive |
| **Data & System Health**| CelesTrak network ping | Probes live CelesTrak endpoint | **PASS** | **PASS** | Safe error handling on cloud timeout |
| **Data & System Health**| Catalog cache inspector | Lists cached TLE files with age, TTL, and SHA-256 | **PASS** | **PASS** | Full provenance tracking |
| **Data & System Health**| Export CSV & TXT report | Generates downloadable encounter reports | **PASS** | **PASS** | Verified CSV headers & TXT summary |
