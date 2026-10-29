# OrbitalGuard AI ? UI Test Matrix & Control Audit

**Project**: OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine  
**Document**: `docs/UI_TEST_MATRIX.md`  
**Execution Environment**: Streamlit 1.45.1, Chromium headless (`AppTest`), Pytest 8.3.4  
**Audit Scope**: Every interactive control across all 7 dashboard pages.  

---

## 1. Global Navigation & Sidebar

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| Sidebar | **Navigate** | Radio | Renders page selection and switches view | Instantly switches between all 7 pages without session loss | `AppTest.sidebar.radio` | **PASS** | `frontend/dashboard.py:46` | None. Responsive and persistent. |

---

## 2. Page 1: Mission Overview

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| Mission overview | Empty state prompt | Information | Informs user to select target if unselected | Displays guidance prompt | Headless AppTest | **PASS** | `frontend/pages/overview.py:16` | Handled cleanly. |
| Mission overview | Target Metric Cards | Display | Shows target name, catalog ID, epoch, origin | Displays exact formatted metadata | `AppTest.metric` | **PASS** | `frontend/pages/overview.py:18-30` | None. |
| Mission overview | Screening Metrics | Display | Shows considered, propagated, flagged, TCA | Displays exact values from `ScreeningRun` | `AppTest.metric` | **PASS** | `frontend/pages/overview.py:38-54` | None. |
| Mission overview | **Failed objects** | Expander | Collapsible table showing failed SGP4 records | Renders SGP4 error code details | Manual / AppTest | **PASS** | `frontend/pages/overview.py:58-60` | Only renders if failures > 0. |

---

## 3. Page 2: Satellite Selection

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| Satellite selection | **Catalog group** | Selectbox | Allows choosing from 18 CelesTrak groups | Selects group, updates `st.session_state` | AppTest selectbox | **PASS** | `frontend/pages/satellite_selection.py:17` | None. |
| Satellite selection | **Search by name** | Text Input | Accepts satellite name query | Receives input string | AppTest text input | **PASS** | `frontend/pages/satellite_selection.py:20` | None. |
| Satellite selection | **Search name** | Button | Queries CelesTrak for matching name | Queries upstream; displays warning if empty or not found | Unit + AppTest | **PASS** | `frontend/pages/satellite_selection.py:21` | Does not replace selected target if query fails. |
| Satellite selection | **Search by catalog ID** | Text Input | Accepts NORAD catalog ID string | Receives integer/string ID | AppTest text input | **PASS** | `frontend/pages/satellite_selection.py:23` | None. |
| Satellite selection | **Search catalog ID** | Button | Queries CelesTrak for specific CATNR | Retrieves exact record; handles 404 | Unit + AppTest | **PASS** | `frontend/pages/satellite_selection.py:24` | Raises `ObjectNotFoundError` cleanly. |
| Satellite selection | **Refresh data** | Button | Bypasses cache and re-queries CelesTrak | Forces fresh download and updates cache | AppTest button click | **PASS** | `frontend/pages/satellite_selection.py:26` | Verified cache update. |
| Satellite selection | **Load catalog group** | Button | Fetches selected group (from cache or live) | Queries CelesTrak with timeout guard; displays fallback if restricted | Integration + AppTest | **PASS** | `frontend/pages/satellite_selection.py:27` | **Fixed**: Added `use_container_width=True` and fallback container. |
| Satellite selection | **Load bundled sample (offline)** | Button | Loads historical 4-satellite sample | Loads ISS, NOAA 15, Iridium, Cosmos | AppTest button click | **PASS** | `frontend/pages/satellite_selection.py:28` | **Fixed**: Widened column ratio to `[2, 2, 2]` to eliminate word-wrapping bug. |
| Satellite selection | **Load offline snapshot** | Button | Loads cached/raw snapshot from disk when network fails | Parses local `.tle` and restores session state | Integration test (`test_satellite_selection_fallback`) | **PASS** | `frontend/pages/satellite_selection.py:89` | **Added**: Provides 1-click fallback during cloud IP timeouts. |
| Satellite selection | **Upload a TLE/3LE text file** | File Uploader | Validates and parses uploaded TLE text | Parses two-line and three-line sets, enforces 2MB limit | Unit + AppTest | **PASS** | `frontend/pages/satellite_selection.py:108` | Rejects malformed records cleanly. |
| Satellite selection | **Filter loaded records** | Text Input | Real-time substring filter on loaded objects | Filters selectbox options by name/ID | AppTest text input | **PASS** | `frontend/pages/satellite_selection.py:126` | Real-time filtering. |
| Satellite selection | **Select target satellite** | Selectbox | Chooses primary target for screening | Stores selected `OrbitalRecord` in session | AppTest selectbox | **PASS** | `frontend/pages/satellite_selection.py:132` | Persists across page navigation. |

---

## 4. Page 3: Conjunction Screening

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| Conjunction screening | **Forecast horizon (hours)** | Selectbox | Configures propagation time (6 to 72h) | Sets propagation end epoch | AppTest selectbox | **PASS** | `frontend/pages/conjunction_screening.py:23` | None. |
| Conjunction screening | **Geometric screening threshold (km)** | Number Input | Sets miss-distance filter threshold | Sets threshold distance for flags | AppTest number input | **PASS** | `frontend/pages/conjunction_screening.py:24` | Validates range [0.1, 5000]. |
| Conjunction screening | **Sampling interval (seconds)** | Slider | Sets coarse grid sampling interval | Adjusts coarse propagation steps | AppTest slider | **PASS** | `frontend/pages/conjunction_screening.py:25` | Validates range [30, 600]. |
| Conjunction screening | **Maximum candidates** | Slider | Bounds number of candidates evaluated | Restricts candidate loop for speed | AppTest slider | **PASS** | `frontend/pages/conjunction_screening.py:32` | Bounded [10, 400]. |
| Conjunction screening | **Start screening** | Button | Executes SGP4 screening run | Propagates orbits, detects local minima, refines TCA | Headless AppTest | **PASS** | `frontend/pages/conjunction_screening.py:35` | Computes refined TCA and miss distance. |
| Conjunction screening | **Refresh catalog then screen** | Button | Refreshes upstream data then executes run | Fetches fresh records then runs screen | Integration test | **PASS** | `frontend/pages/conjunction_screening.py:36` | Handles upstream errors cleanly. |
| Conjunction screening | **Filter candidates by name or catalog ID** | Text Input | Filters table by candidate name/ID | Filters displayed approaches dataframe | AppTest text input | **PASS** | `frontend/pages/conjunction_screening.py:76` | Added candidate search filter. |
| Conjunction screening | **Only show within-threshold flags** | Checkbox | Toggles display of threshold-exceeding pairs | Filters table to `within_threshold == True` | AppTest checkbox | **PASS** | `frontend/pages/conjunction_screening.py:78` | Filter operates dynamically. |
| Conjunction screening | **Filter: max displayed sep (km)** | Slider | Interactively clips table rows by distance | Filters table interactively | AppTest slider | **PASS** | `frontend/pages/conjunction_screening.py:80` | Handles dynamic min/max. |
| Conjunction screening | **Candidate detail** | Selectbox | Selects candidate approach for inspection | Selects approach and updates plots | AppTest selectbox | **PASS** | `frontend/pages/conjunction_screening.py:89` | Persists `selected_approach`. |
| Conjunction screening | Separation Histogram | Plotly Chart | Shows miss distance distribution | Renders interactive Plotly histogram | AppTest chart check | **PASS** | `frontend/pages/conjunction_screening.py:93` | Validated Plotly figure. |
| Conjunction screening | Separation & Velocity vs Time | Plotly Charts | Shows miss distance and relative speed curves | Renders time-series around TCA | Integration test | **PASS** | `frontend/pages/conjunction_screening.py:145` | **Fixed**: Replaced `add_vline` with `add_shape` to prevent datetime bug. |

---

## 5. Page 4: Orbital Visualization

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| Orbital visualization | **Candidate trajectory** | Selectbox | Chooses secondary orbit to render in 3D | Selects candidate object for comparison | AppTest selectbox | **PASS** | `frontend/pages/orbital_visualization.py:30` | Falls back to first candidate if none selected. |
| Orbital visualization | **Trajectory samples** | Slider | Sets number of 3D orbital trajectory steps | Adjusts spline resolution [20, 180] | AppTest slider | **PASS** | `frontend/pages/orbital_visualization.py:36` | Configures resolution. |
| Orbital visualization | **Time index** | Slider | Steps through time along propagated orbit | Updates satellite marker positions | AppTest slider | **PASS** | `frontend/pages/orbital_visualization.py:38` | Updates state dictionary. |
| Orbital visualization | 3D Orbital Trajectory Plot | Plotly Chart | Renders TEME coordinates with Earth sphere | Interactive WebGL 3D orbit render | AppTest chart check | **PASS** | `frontend/pages/orbital_visualization.py:43` | Correctly labeled as inertial TEME frame. |

---

## 6. Page 5: Risk Assessment

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---|:---|:---|
| Risk assessment | Geometric proximity section | Display | Displays miss distance, TCA, v_rel | Displays exact values with units | AppTest display check | **PASS** | `frontend/pages/risk_assessment.py:27-36` | Clearly labeled as geometric flag. |
| Risk assessment | Heuristic screening score | Display | Displays 0-100 score and 70/15/15 weights | Shows transparent formula and score | AppTest display check | **PASS** | `frontend/pages/risk_assessment.py:38-51` | Explicitly marked `not_a_probability`. |
| Risk assessment | Statistical $P_c$ section | Display | Displays gating status and explanation | Displays `unavailable` with explanation | AppTest metric check | **PASS** | `frontend/pages/risk_assessment.py:53-57` | **Strict Rule**: Never fabricates covariance. |
| Risk assessment | ML proxy score section | Display | Displays proxy score if artifact loaded | Shows `below_threshold_proxy` score | AppTest display check | **PASS** | `frontend/pages/risk_assessment.py:59-71` | Explicitly marked `not_collision_probability`. |
| Risk assessment | Assumptions expander | Expander | Lists operational and physical limits | Expands and displays limitations | AppTest expander | **PASS** | `frontend/components.py:90` | Clearly readable. |

---

## 7. Page 6: ML Model Evaluation

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| ML model evaluation | Model status card | Display | Shows model type, target definition, split | Displays logistic regression metadata | AppTest display check | **PASS** | `frontend/pages/model_evaluation.py:40-50` | Reflects loaded artifact. |
| ML model evaluation | Metric comparison columns | Display | Compares ML model vs physical vs dummy | Displays precision, recall, F1, accuracy | AppTest display check | **PASS** | `frontend/pages/model_evaluation.py:55-70` | Grounded in held-out test set ($N=36$). |
| ML model evaluation | Confusion matrix | Plotly Chart | Renders 2x2 confusion matrix heatmap | Renders interactive Plotly heatmap | AppTest chart check | **PASS** | `frontend/pages/model_evaluation.py:73` | Exact TP, FP, TN, FN counts. |
| ML model evaluation | Feature coefficients | Plotly Chart | Renders bar chart of model weights | Renders interactive horizontal bar chart | AppTest chart check | **PASS** | `frontend/pages/model_evaluation.py:78` | Scaled weights. |
| ML model evaluation | **Raw metadata** | Expander | Shows JSON metadata of trained pipeline | Collapsible code block with JSON | AppTest expander | **PASS** | `frontend/pages/model_evaluation.py:82` | Full provenance tracking. |

---

## 8. Page 7: Data and System Health

| Page | Control Label | Type | Expected Behavior | Actual Behavior | Test Method | Result | Code Location | Defects & Fixes |
|:---|:---|:---:|:---|:---|:---:|:---:|:---|:---|
| Data and system health | **Refresh diagnostics** | Button | Re-checks system status and updates time | Updates timestamp in session state | AppTest button click | **PASS** | `frontend/pages/system_health.py:20` | Responsive. |
| Data and system health | **Ping CelesTrak stations (network)** | Button | Live network probe to CelesTrak endpoint | Probes CelesTrak; reports status/count | Integration test | **PASS** | `frontend/pages/system_health.py:22` | Catches exceptions safely without crash. |
| Data and system health | **Export CSV and text report** | Button | Generates and exports CSV and TXT files | Writes files to `data/processed/` | Integration test (`test_end_to_end`) | **PASS** | `frontend/pages/system_health.py:65` | Verified file generation and contents. |
| Data and system health | **Download CSV** | Download Button | Serves generated CSV to user | Streams CSV file content | Integration test | **PASS** | `frontend/pages/system_health.py:70` | Verified valid CSV headers and data. |
| Data and system health | **Download text report** | Download Button | Serves generated TXT summary to user | Streams formatted text summary | Integration test | **PASS** | `frontend/pages/system_health.py:71` | Verified TXT report with 70/15/15 breakdown. |
| Data and system health | Catalog cache table | Dataframe | Lists cached `.tle` files with SHA-256 | Renders interactive table of cache files | AppTest dataframe | **PASS** | `frontend/pages/system_health.py:38` | Shows age, freshness, SHA-256. |

---

## 9. Conclusion
All interactive controls across the entire 7-page dashboard have been audited, exercised through automated testing, and verified functional. All edge cases (empty states, missing network, invalid inputs, large catalogs) are handled gracefully without application crashes.
