# OrbitalGuard AI ? Complete Beginner's Technical Guide & Viva Handbook

Welcome to the comprehensive technical documentation and beginner's guide for **OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine**.

This guide is designed for engineering students, researchers, developers, viva examiners, and space enthusiasts. It assumes zero prior background in aerospace engineering, orbital mechanics, or advanced machine learning.

---

# Table of Contents
1. [Section 1 ? Project Overview](#section-1--project-overview)
2. [Section 2 ? The Problem Statement](#section-2--the-problem-statement)
3. [Section 3 ? The Complete Proposed Solution](#section-3--the-complete-proposed-solution)
4. [Section 4 ? Dataset and Data-Source Explanation](#section-4--dataset-and-data-source-explanation)
5. [Section 5 ? Technologies, Programming Languages, and Libraries](#section-5--technologies-programming-languages-and-libraries)
6. [Section 6 ? Project Folder and File Architecture](#section-6--project-folder-and-file-architecture)
7. [Section 7 ? Orbital Mechanics Explained from Zero](#section-7--orbital-mechanics-explained-from-zero)
8. [Section 8 ? Risk Assessment Explained Simply](#section-8--risk-assessment-explained-simply)
9. [Section 9 ? Machine Learning Explained from Zero](#section-9--machine-learning-explained-from-zero)
10. [Section 10 ? Dashboard & UI Walkthrough](#section-10--dashboard--ui-walkthrough)
11. [Section 11 ? Windows Installation and Execution Guide](#section-11--windows-installation-and-execution-guide)
12. [Section 12 ? Testing, Quality Assurance, and Verification](#section-12--testing-quality-assurance-and-verification)
13. [Section 13 ? Limitations and Future Scope](#section-13--limitations-and-future-scope)
14. [Section 14 ? Comprehensive Viva and Technical Interview Preparation (35 Questions)](#section-14--comprehensive-viva-and-technical-interview-preparation-35-questions)
15. [Section 15 ? Glossary and Quick Revision Sheet](#section-15--glossary-and-quick-revision-sheet)

---

# Section 1 ? Project Overview

### 1.1 What is OrbitalGuard AI?
**OrbitalGuard AI** is a Python-based aerospace research and educational application built to monitor, propagate, and forecast close encounters between satellites and orbiting space debris.

### 1.2 What is Space Debris?
When humanity launches rockets, satellites, and scientific probes into space, not everything returns to Earth. Over the past 65+ years since Sputnik (1957), tens of thousands of artificial objects have accumulated in Earth orbit:
- Defunct satellites that ran out of fuel or electrical power.
- Spent upper stages of launch vehicles (rocket booster bodies).
- Fragmentation debris created when old satellites exploded or collided (e.g., the 2009 collision between Iridium 33 and Kosmos 2251, or anti-satellite missile tests).
- Abandoned equipment, lens caps, and tiny flecks of peeling paint.

Because objects in Low Earth Orbit (LEO) travel at hypervelocity?roughly **7.5 kilometres per second (27,000 km/h or 17,500 mph)**?even a 1-centimetre metal fragment carries the explosive kinetic energy of a hand grenade. A collision between two satellites can shatter both into thousands of untracked pieces, creating a cascade effect known as the **Kessler Syndrome**.

### 1.3 What Problem Does OrbitalGuard AI Solve?
Every day, satellite operators (like ISRO, NASA, ESA, Planet Labs, Starlink) must determine whether any cataloged debris will pass dangerously close to their active spacecraft. This is called **conjunction assessment**.
OrbitalGuard AI solves the problem of automated geometric close-approach screening:
1. It ingests public orbital element sets (Two-Line Elements, or TLEs).
2. It propagates orbits forward in time using standard mathematical theories (SGP4).
3. It identifies the exact moment of closest approach (TCA) and calculates the minimum miss distance.
4. It computes the relative speed between the objects.
5. It ranks candidate hazards using a transparent heuristic scoring formula.
6. It demonstrates how machine learning can predict proxy proximity labels without leaking future target information.

### 1.4 What Problem Does It NOT Solve?
**OrbitalGuard AI is an academic research prototype, not a military-grade or certified operational collision avoidance system.**
- It does **not** predict that two satellites *will definitely collide*.
- It does **not** command satellite thrusters or execute automated avoidance maneuvers.
- It does **not** claim to compute statistical collision probabilities ($P_c$) because public TLEs lack the necessary covariance uncertainty matrices.

### 1.5 A Simple Analogy: Highway Radar vs Crystal Ball
Imagine driving a car on a highway in dense fog:
- A radar scanner can tell you: *"A truck is 500 meters ahead of you moving at 100 km/h, and your relative speed is 20 km/h."* This is **geometric proximity screening**.
- The radar cannot tell you: *"There is a 94.2% chance you will crash in 30 seconds."* To say that, you would need to know the driver's exact steering accuracy, lane width, tire friction, and wind gusts (which is **covariance uncertainty**).
OrbitalGuard AI acts as the honest highway radar: it provides accurate relative geometry and tells you honestly when uncertainty data is unavailable.

---

# Section 2 ? The Problem Statement

### 2.1 Formal Problem Statement
> *"Given a target satellite and a candidate population of cataloged orbital objects described by NORAD General Perturbations orbital elements, design and implement an end-to-end, scientifically defensible software engine to: ingest and validate public orbital data; propagate trajectories over a configurable forecast horizon (6 to 72 hours) in the TEME reference frame using the SGP4 theory; screen for potential conjunctions; numerically refine the Time of Closest Approach (TCA) and minimum miss distance; evaluate relative velocities; apply a transparent proximity ranking heuristic; enforce rigorous statistical gates that reject unverified collision probabilities; evaluate a leakage-resistant machine-learning proxy classifier; and visualize encounter geometry in an interactive dashboard."*

### 2.2 Why Orbital Tracking is Challenging
1. **Catalog Scale**: There are over 25,000 tracked objects larger than 10 cm in orbit, and hundreds of thousands of smaller fragments. Comparing every object against every other object ($N 	imes N$) produces hundreds of millions of pairs.
2. **Computational Limits**: Orbit propagation requires numerical or analytical integration over thousands of steps. Coarse screening filters are required before fine refinement.
3. **Orbital Perturbations**: The Earth is not a perfect sphere (it bulges at the equator, creating the $J_2$ gravitational harmonic). Atmospheric drag constantly pulls LEO satellites down. The Moon, the Sun, and solar radiation pressure constantly perturb orbits.
4. **Data Degradation**: A TLE element set is a snapshot fitted at a specific time (its epoch). As days pass, the SGP4 propagation error grows from hundreds of meters to tens of kilometres per day.

---

# Section 3 ? The Complete Proposed Solution

### 3.1 End-to-End System Data Flow
```
[ CelesTrak GP / Custom Upload / Offline Sample ]
                        ?
                        ?
            [ TLEValidationService ]
         (Checksum, Line Layout, Epoch)
                        ?
                        ?
             [ DataSourceService ]
          (TTL Cache, Manifests, Retries)
                        ?
                        ?
         [ OrbitalPropagationService ]
          (SGP4 / SDP4 in TEME frame)
                        ?
                        ?
        [ ConjunctionScreeningService ]
        ??? Coarse Grid Evaluation
        ??? Local Minima Isolation
        ??? Golden-Section Bounded TCA Refinement
                        ?
                        ?
            [ RiskAssessmentService ]
        ??? 1. Geometric Proximity
        ??? 2. Heuristic Ranking Score (0-100)
        ??? 3. Statistical Pc Gate (UNAVAILABLE)
                        ?
                        ?
         [ FeatureEngineeringService ]
          (Kinematic Features at t0)
                        ?
                        ?
          [ ModelPredictionService ]
       (Logistic Regression on Proxy Target)
                        ?
                        ?
        [ Streamlit UI & Report Exporter ]
         (7 Interactive Pages, CSV & TXT)
```

### 3.2 Stage-by-Stage Breakdown
| Stage | What It Does | Why Needed | Inputs | Outputs | Implementing Source File |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Data Ingestion** | Fetches TLEs from CelesTrak or user upload | Obtains orbital elements | Satellite Name or Catalog ID | Raw text data | `backend/data_sources.py` |
| **2. TLE Parsing** | Validates line syntax, checksum, epoch | Rejects corrupt data | Raw text | `OrbitalRecord` objects | `backend/tle_parser.py` |
| **3. Propagation** | SGP4 evaluates position and velocity | Predicts future orbit | `OrbitalRecord`, requested UTC times | TEME Cartesian vectors ($ec{r}, ec{v}$) | `backend/orbital_propagation.py` |
| **4. Screening** | Computes $\|ec{r}_2 - ec{r}_1\|$ across time | Detects close passes | Target & Candidate trajectories | Coarse candidate encounters | `backend/conjunction_screening.py` |
| **5. TCA Refinement** | Minimizes range numerically | Locates exact closest time | Time bracket $[t_0 - \Delta t, t_0 + \Delta t]$ | Refined TCA, min separation (km) | `backend/conjunction_screening.py` |
| **6. Risk Assessment** | Scores proximity, gates $P_c$ | Prioritizes hazards safely | Miss distance, relative speed, age | Heuristic score (0-100), $P_c$ status | `backend/risk_assessment.py` |
| **7. Feature Engineering** | Extracts physical features at $t_0$ | Feeds ML without future leakage | $t_0$ orbital states, inclinations | ML feature row | `backend/feature_engineering.py` |
| **8. ML Prediction** | Evaluates trained classifier | Demonstrates proxy classification | Feature row | `ml_proxy_score` (0.0 to 1.0) | `backend/prediction_service.py` |
| **9. Dashboard** | Renders tables, 3D orbits, plots | User interaction & export | ScreeningRun state | 7 UI pages, CSV/TXT files | `frontend/dashboard.py` |

---

# Section 4 ? Dataset and Data-Source Explanation

### 4.1 Where Does the Data Come From?
The primary data source is **CelesTrak** (curated by Dr. T.S. Kelso), which mirrors orbital data published by the United States Space Force (18th Space Defense Squadron via Space-Track.org).

CelesTrak provides an open HTTP General Perturbations (GP) query interface:
`https://celestrak.org/NORAD/elements/gp.php?{QUERY}={VALUE}&FORMAT=TLE`

Query parameters supported:
- `GROUP=visual` (bright visual satellites)
- `GROUP=stations` (space stations including ISS, Tiangong)
- `GROUP=active` (active operational satellites)
- `GROUP=debris` (cataloged debris pieces)
- `NAME={name}` (e.g. `NAME=ISS`)
- `CATNR={catalog_id}` (e.g. `CATNR=25544`)

### 4.2 What is a Two-Line Element Set (TLE)?
A TLE is a standard 2-line ASCII text format encoding the mathematical parameters needed by the SGP4 algorithm to compute a satellite's position and velocity at any time.

Here is a real example of the International Space Station (ISS):
```
ISS (ZARYA)
1 25544U 98067A   19343.69339541  .00001764  00000-0  38792-4 0  9991
2 25544  51.6439 211.2001 0007417  17.6667  85.6398 15.50103472202482
```

Let's break down what every character means:
- **Line 0**: `ISS (ZARYA)` ? Satellite name.
- **Line 1, Col 1**: `1` ? Line number.
- **Line 1, Col 3-7**: `25544` ? NORAD Catalog Identifier (assigned to ISS).
- **Line 1, Col 8**: `U` ? Security classification (`U` = Unclassified).
- **Line 1, Col 10-17**: `98067A` ? International Designator (COSPAR ID: Year 1998, Launch #067, Piece A).
- **Line 1, Col 19-32**: `19343.69339541` ? **Element Epoch** (Year 2019, Day 343.69339541 = Dec 9, 2019, ~16:38 UTC).
- **Line 1, Col 34-43**: `.00001764` ? First derivative of mean motion divided by 2 (ballistic coefficient drag term).
- **Line 1, Col 45-52**: `00000-0` ? Second derivative of mean motion (usually zero).
- **Line 1, Col 54-61**: `38792-4` ? **$B^*$ (B-Star) Drag Term** ($0.38792 \times 10^{-4}$ Earth radii$^{-1}$). Models atmospheric drag.
- **Line 1, Col 63**: `0` ? Ephemeris type.
- **Line 1, Col 65-68**: `999` ? Element set number.
- **Line 1, Col 69**: `1` ? Modulo-10 Checksum of Line 1.

- **Line 2, Col 1**: `2` ? Line number.
- **Line 2, Col 3-7**: `25544` ? Matching catalog number.
- **Line 2, Col 9-16**: `51.6439` ? **Inclination ($i$) in degrees**. The tilt of the orbital plane relative to the equator.
- **Line 2, Col 18-25**: `211.2001` ? **Right Ascension of the Ascending Node (RAAN, $\Omega$) in degrees**. The angle where the orbit crosses the equator from South to North.
- **Line 2, Col 27-33**: `0007417` ? **Eccentricity ($e$)** (decimal point implied: $0.0007417$). Describes how non-circular the orbit is ($0$ = circle).
- **Line 2, Col 35-42**: `17.6667` ? **Argument of Perigee ($\omega$) in degrees**. The angle to the orbit's closest point to Earth.
- **Line 2, Col 44-51**: `85.6398` ? **Mean Anomaly ($M$) in degrees**. Where the satellite is along its orbit at epoch.
- **Line 2, Col 53-63**: `15.50103472` ? **Mean Motion ($n$) in revolutions per day**. ISS completes $\approx 15.5$ orbits per day ($pprox 93$ minutes per orbit).
- **Line 2, Col 64-68**: `20248` ? Revolution number at epoch.
- **Line 2, Col 69**: `2` ? Modulo-10 Checksum of Line 2.

### 4.3 Checksum Calculation
The checksum validates that no characters were corrupted during transmission:
1. Every numeric digit (0-9) adds its face value.
2. Every minus sign (`-`) adds 1.
3. Letters, periods, spaces, and plus signs add 0.
4. The final sum modulo 10 must equal the last character on the line.

### 4.4 Data Provenance and Caching
- **Raw Storage**: Downloaded TLE files are stored in `data/raw/` with UTC timestamped filenames (e.g., `visual_20261013T043534Z.tle`).
- **Disk Cache**: CelesTrak HTTP responses are hashed with SHA-256 and cached in `data/cache/` with a default 6-hour Time-to-Live (TTL).
- **Provenance Manifests**: Stored in `data/manifests/` detailing retrieval timestamp, URL, SHA-256 hash, and record count.
- **Historical Snapshots**: Periodic cron downloads stored in `data/historical/` via `scripts/collect_snapshot.py`.

---

# Section 5 ? Technologies, Programming Languages, and Libraries

| Technology / Library | What It Is | Why This Project Uses It | Where Used in Code | Beginner Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **Python 3.11 - 3.13** | Programming language | Core language for scientific computing, aerospace tools, and rapid prototyping. | Entire repository | The primary language that runs all calculations and user interfaces. |
| **Streamlit** | Web application framework | Creates reactive, interactive data dashboards directly in pure Python without writing HTML/CSS/JavaScript. | `app.py`, `frontend/` | Turns Python scripts into a shareable web app with buttons, sliders, and charts. |
| **Plotly** | Data visualization library | Generates hardware-accelerated interactive 3D WebGL plots and charts with zooming, panning, and hovering. | `frontend/visualizations.py` | Draws the interactive 3D Earth, satellite orbit paths, and encounter graphs. |
| **SGP4** | Python orbital propagator | Official Python binding of David Vallado's canonical C++ Simplified General Perturbations 4 algorithm. | `backend/orbital_propagation.py` | Takes TLE orbital elements and computes where a satellite will be at any future second. |
| **NumPy** | Numerical array library | High-speed vectorized mathematical operations on matrices, 3D Cartesian vectors, and norms. | `backend/coordinate_utils.py`, `conjunction_screening.py` | Fast math library that calculates vector distances and velocities in microsecond speed. |
| **pandas** | Data analysis library | Manages tabular data structures (DataFrames), CSV import/export, filtering, and grouping. | `ml/`, `frontend/`, `report_service.py` | Like Excel spreadsheets inside Python code; filters rows and calculates summary statistics. |
| **SciPy** | Scientific algorithms | Provides `scipy.optimize.minimize_scalar` for 1D bounded numerical optimization. | `backend/conjunction_screening.py` | Finds the exact mathematical minimum distance between two orbits. |
| **scikit-learn** | Machine learning library | Provides preprocessing pipelines (`SimpleImputer`, `StandardScaler`) and classifiers (`LogisticRegression`). | `ml/train_baseline.py`, `evaluate_model.py` | Builds and evaluates AI/ML models on clean numerical feature vectors. |
| **joblib** | Serialization library | Safely serializes and deserializes Python objects, trained ML pipelines, and metadata dictionaries. | `backend/prediction_service.py`, `ml/train_baseline.py` | Saves trained AI models to a file so they can be loaded instantly without retraining. |
| **Pydantic** | Data validation library | Enforces strict static type schemas on data models and parameters. | `backend/models.py` | Ensures every satellite record has valid names, IDs, dates, and numbers. |
| **requests** | HTTP networking library | Handles secure HTTP GET requests to CelesTrak with timeout and retry controls. | `backend/data_sources.py` | Downloads live satellite data over the internet from CelesTrak servers. |
| **pytest** | Automated test framework | Executes automated unit, integration, and UI regression tests with detailed assertion failure reports. | `tests/` | Automatically tests every piece of code to guarantee no bugs or math errors exist. |

---

# Section 6 ? Project Folder and File Architecture

```
orbitalguard-ai/
??? app.py                      # Main entry point: launches the Streamlit web app
??? requirements.txt            # List of all Python packages required by the project
??? README.md                   # Quick-start manual and Windows PowerShell guide
??? pytest.ini                  # Pytest test path configuration
??? .env.example                # Template showing configurable environment variables
??? .gitignore                  # Tells Git which temporary files and virtual environments to ignore
??? config/
?   ??? __init__.py             # Makes config a Python package
?   ??? settings.py             # Global settings dataclass: file paths, thresholds, cache TTL
??? backend/
?   ??? __init__.py
?   ??? models.py               # Data structures (OrbitalRecord, ApproachResult, ScreeningRun)
?   ??? exceptions.py           # Custom error classes (PropagationError, ChecksumError, etc.)
?   ??? data_sources.py         # CelesTrak client, retry logic, disk cache, upload parser
?   ??? tle_parser.py           # TLE line parser, modulo-10 checksum verifier, epoch converter
?   ??? orbital_propagation.py  # SGP4 engine returning TEME positions and velocities
?   ??? coordinate_utils.py     # Relative math: dr, dv, miss distance, relative speed
?   ??? conjunction_screening.py# Coarse screening + Golden-Section bounded TCA refinement
?   ??? risk_assessment.py      # Computes heuristic score (0-100) and gates Pc as unavailable
?   ??? feature_engineering.py  # Builds kinematic feature vectors at start epoch t0
?   ??? prediction_service.py   # Loads local ML artifact and scores feature rows
?   ??? report_service.py       # Exports screening results as CSV and TXT audit reports
?   ??? logging_utils.py        # Structured logging to console and logs/orbitalguard.log
??? frontend/
?   ??? __init__.py
?   ??? dashboard.py            # Streamlit multi-page layout, sidebar router, space theme CSS
?   ??? components.py           # Reusable UI widgets: metric cards, status badges, previews
?   ??? visualizations.py       # Plotly figures: 3D TEME orbits, distance curves, heatmaps
?   ??? pages/
?       ??? __init__.py
?       ??? overview.py         # Page 1: Mission overview and telemetry summary
?       ??? satellite_selection.py # Page 2: Satellite search, group loader, upload, bundled sample
?       ??? conjunction_screening.py # Page 3: Screening controls, sortable table, candidate detail
?       ??? orbital_visualization.py # Page 4: Interactive 3D Earth and orbit visualizer
?       ??? risk_assessment.py  # Page 5: Risk concept breakdown (Geometry vs Heuristic vs Pc)
?       ??? model_evaluation.py # Page 6: ML metrics, feature importance, confusion matrix
?       ??? system_health.py    # Page 7: Diagnostics, data freshness, error logs, report export
??? ml/
?   ??? __init__.py
?   ??? build_dataset.py        # Generates proxy dataset with deduplicated canonical pairs
?   ??? validation.py           # Grouped chronological holdout partitioner (no leakage)
?   ??? train_baseline.py       # Trains LogisticRegression pipeline vs physical/dummy baselines
?   ??? evaluate_model.py       # Computes Precision, Recall, F1, PR-AUC, ROC-AUC, Brier score
?   ??? predict.py              # Command-line utility to score CSV files with trained model
??? models/artifacts/           # Serialized joblib model artifacts and metadata
??? ml/artifacts/               # Synchronized copy of model artifacts
??? data/
?   ??? raw/                    # Raw downloaded TLE snapshots
?   ??? processed/              # Processed CSV datasets and schemas
?   ??? historical/             # Historical archive snapshots from collect_snapshot.py
?   ??? manifests/              # Retrieval provenance JSON files
?   ??? cache/                  # SHA-256 hashed CelesTrak responses
?   ??? sample_metadata/        # Bundled offline sample catalog (ISS, NOAA 15, Envisat, Vanguard 1)
??? tests/
?   ??? conftest.py             # Pytest fixtures: ISS, Vanguard 1, Benchmark 88888, sample data
?   ??? test_tle_parser.py      # Tests TLE layout, checksums, duplicates, malformed files
?   ??? test_data_sources.py    # Tests CelesTrak client, mocked HTTP, retries, caching
?   ??? test_orbital_propagation.py # Tests SGP4 against Vallado benchmark Sat 5 and Sat 88888
?   ??? test_coordinate_utils.py # Tests vector subtraction, altitudes, Julian date conversions
?   ??? test_conjunction_screening.py # Tests coarse screening, local minima, TCA refinement
?   ??? test_risk_assessment.py # Tests heuristic score range (0-100) and Pc gate enforcement
?   ??? test_feature_engineering.py # Tests feature shapes, units, and column schemas
?   ??? test_dataset_pipeline.py # Tests snapshot ingestion and proxy dataset synthesis
?   ??? test_model_validation.py # Tests grouped holdout splitting and untrusted artifact rejection
?   ??? test_ml_validation.py   # Tests chronological grouping constraints
?   ??? test_report_and_prediction.py # Tests CSV/TXT exports and prediction service lifecycle
?   ??? test_integration.py     # End-to-end workflow + headless Streamlit AppTest multi-page run
??? scripts/
?   ??? download_catalog.py     # CLI script to download CelesTrak catalog groups
?   ??? collect_snapshot.py     # CLI script to build historical archive snapshots
?   ??? run_preflight.py        # Verifies Python environment, packages, and directory tree
??? docs/                       # Technical reports, data dictionaries, research notes, and manuals

---

# Section 7 ? Orbital Mechanics Explained from Zero

### 7.1 What is an Orbit?
An orbit is the curved trajectory of an object around a massive celestial body (like Earth) governed by gravity.
As Isaac Newton discovered in his famous cannonball thought experiment:
If you fire a cannon horizontally from a high mountain:
- At low speed, gravity pulls the ball down and it crashes into the ground.
- At higher speed, it travels further before hitting the ground.
- At an exact critical speed?approximately **7.8 kilometres per second**?the ground curves away beneath the cannonball at the exact same rate that gravity pulls it downward! The cannonball is in continuous, perpetual free-fall around the Earth without ever hitting the ground. This is an **orbit**.

### 7.2 The Classical Keplerian Orbital Elements
Johannes Kepler established that planetary orbits are ellipses with the central body at one focus. To describe an orbit in 3D space, we need 6 fundamental numbers:
1. **Semi-Major Axis ($a$)**: The size of the orbit (half of the longest diameter). In TLEs, this is represented by Mean Motion ($n$), since $n = \sqrt{\mu / a^3}$ (Kepler's Third Law).
2. **Eccentricity ($e$)**: The shape of the orbit ($e = 0$ is a circle, $0 < e < 1$ is an ellipse).
3. **Inclination ($i$)**: The tilt of the orbital plane relative to Earth's equatorial plane ($0^\circ$ is equatorial, $90^\circ$ is polar, $>90^\circ$ is retrograde).
4. **Right Ascension of the Ascending Node (RAAN, $\Omega$)**: The orientation of the orbital plane in space, measured from the Vernal Equinox (First Point of Aries).
5. **Argument of Perigee ($\omega$)**: The orientation of the ellipse in the orbital plane, measured from the ascending node to the closest point to Earth (perigee).
6. **True Anomaly ($\nu$) or Mean Anomaly ($M$)**: The angular position of the satellite along its orbit at a specific moment in time (epoch).

### 7.3 What is SGP4?
**SGP4 (Simplified General Perturbations 4)** is a mathematical theory developed in 1970 by Felix Hoots and Ronald Roehrich at the North American Aerospace Defense Command (NORAD).
SGP4 is an **analytical propagator**, meaning it evaluates closed-form mathematical equations rather than performing step-by-step numerical integration. It incorporates:
- Earth's non-spherical gravitational bulge ($J_2$, $J_3$, $J_4$ zonal harmonics).
- Atmospheric drag using a simplified atmospheric density profile and the satellite's $B^*$ drag parameter.
- For deep-space objects with orbital periods $\ge 225$ minutes, the extended **SDP4** theory automatically adds lunar and solar gravitational perturbations.

### 7.4 The TEME Coordinate Frame
SGP4 outputs satellite positions and velocities in a specific astronomical reference frame called:
**True Equator, Mean Equinox (TEME)**.
- **Origin**: Center of mass of the Earth.
- **Fundamental Plane**: Earth's True Equator (accounting for nutation).
- **Primary Direction ($X$-axis)**: Mean Vernal Equinox (accounting for precession).
- **$Z$-axis**: Earth's True Rotation Pole.
- **$Y$-axis**: Completes a right-handed orthogonal system ($90^\circ$ East along the equator).

> **CRITICAL RULE**: Because TEME is a non-rotating inertial frame, positions and velocities must NEVER be compared directly with Earth-Fixed (ITRF/ECEF) coordinates without applying the Earth rotation angle (Greenwich Apparent Sidereal Time, GAST). OrbitalGuard AI computes all relative quantities strictly between TEME vectors at the identical UTC timestamp.

### 7.5 Conjunction Screening Mathematics
For Target satellite 1 and Candidate satellite 2 at identical UTC timestamp $t$:
$$\Delta \vec{r}(t) = \vec{r}_2(t) - \vec{r}_1(t) \quad [\text{kilometres}]$$
$$\Delta \vec{v}(t) = \vec{v}_2(t) - \vec{v}_1(t) \quad [\text{kilometres per second}]$$
$$d(t) = \|\Delta \vec{r}(t)\| = \sqrt{\Delta x^2 + \Delta y^2 + \Delta z^2} \quad [\text{kilometres}]$$
$$v_{\text{rel}}(t) = \|\Delta \vec{v}(t)\| = \sqrt{\Delta v_x^2 + \Delta v_y^2 + \Delta v_z^2} \quad [\text{kilometres per second}]$$

### 7.6 Why Coarse Grid Sampling is Not Enough (The Need for TCA Refinement)
If you sample satellite positions every 120 seconds:
Two satellites moving at relative speed $v_{\text{rel}} = 14\text{ km/s}$ travel **1,680 kilometres** between samples!
If the exact closest encounter happened at second 64, sampling at second 0 and second 120 might show a separation of 400 km, while at second 64 they passed within 500 meters!
Therefore, OrbitalGuard AI uses a two-stage screening process:
1. **Coarse Pass**: Evaluates range $d(t)$ along a uniform time grid.
2. **Local Minima Search**: Identifies every index $i$ where $d_i \le d_{i-1}$ and $d_i \le d_{i+1}$.
3. **Bounded Numerical Refinement**: Brackets each local minimum within $[t_{i-1}, t_{i+1}]$ and uses SciPy's Golden-Section scalar optimizer (`minimize_scalar(method='bounded')`) with tolerance `xatol=0.05` seconds to converge onto the exact Time of Closest Approach (TCA) and true minimum miss distance.

---

# Section 8 ? Risk Assessment Explained Simply

OrbitalGuard AI strictly enforces the separation of three distinct concepts:

### 8.1 Concept 1: Geometric Proximity
- **Definition**: The computed physical distance between the two centers of mass at TCA: $d_{\text{min}} = \|\vec{r}_2(\text{TCA}) - \vec{r}_1(\text{TCA})\|$.
- **Comparison**: If $d_{\text{min}} \le \text{threshold}$, the candidate is flagged as `within_threshold`.
- **Meaning**: This is a purely geometric screening flag. It simply means: *"These two objects pass close to each other in our mathematical model."* It is **not** a collision.

### 8.2 Concept 2: The Heuristic Ranking Score (0 to 100)
When an operator screens 500 satellites, 40 of them might pass within a 50 km screening volume. Which ones should the operator investigate first?
OrbitalGuard AI calculates an interpretable, transparent ranking score from 0 (lowest priority) to 100 (highest priority):

$$\text{Score} = 100 \times \left( 0.70 \cdot S_{\text{sep}} + 0.15 \cdot S_{\text{vel}} + 0.15 \cdot S_{\text{fresh}} \right)$$

Where each term is normalized and clipped between $0.0$ and $1.0$:
1. **Separation Term ($70\%$)**:
   $$S_{\text{sep}} = \text{clip}\left(1.0 - \frac{d_{\text{min}}}{\text{threshold}},\; 0.0,\; 1.0\right)$$
   - If $d_{\text{min}} = 0$ km: $S_{\text{sep}} = 1.0$ (maximum danger).
   - If $d_{\text{min}} = \text{threshold}$: $S_{\text{sep}} = 0.0$ (at boundary).
   - If $d_{\text{min}} > \text{threshold}$: $S_{\text{sep}} = 0.0$.

2. **Relative Velocity Term ($15\%$)**:
   $$S_{\text{vel}} = \text{clip}\left(\frac{v_{\text{rel}}}{15.0\text{ km/s}},\; 0.0,\; 1.0\right)$$
   - Scaled against $15\text{ km/s}$ (typical maximum LEO head-on collision speed). Faster relative velocity gives less reaction time and creates higher kinetic energy.

3. **Data Freshness Term ($15\%$)**:
   $$S_{\text{fresh}} = \text{clip}\left(1.0 - \frac{\max(\text{age}_1, \text{age}_2)}{72.0\text{ hours}},\; 0.0,\; 1.0\right)$$
   - Scaled against 72 hours. Fresher TLEs have higher confidence; stale TLEs (>72 hours old) receive zero freshness bonus because SGP4 errors may be large.

#### Hypothetical Calculation Example:
Suppose:
- Screening threshold = $50.0\text{ km}$
- Minimum miss distance $d_{\text{min}} = 10.0\text{ km}$
- Relative speed $v_{\text{rel}} = 12.0\text{ km/s}$
- Target element age = $12.0\text{ hours}$, Candidate age = $24.0\text{ hours}$ (max = $24.0\text{ h}$)

Calculation:
1. $S_{\text{sep}} = 1.0 - \frac{10.0}{50.0} = 0.800$
2. $S_{\text{vel}} = \frac{12.0}{15.0} = 0.800$
3. $S_{\text{fresh}} = 1.0 - \frac{24.0}{72.0} = 0.667$
$$\text{Score} = 100 \times (0.70 \times 0.800 + 0.15 \times 0.800 + 0.15 \times 0.667)$$
$$\text{Score} = 100 \times (0.560 + 0.120 + 0.100) = 78.0 / 100$$

> **VIVA EMPHASIS**: The score is $78.0$ out of $100$. This does NOT mean a $78\%$ chance of collision! It means: *"On our geometric ranking scale, this encounter deserves priority attention."*

### 8.3 Concept 3: Statistical Collision Probability ($P_c$)
To calculate an authentic collision probability (such as $P_c = 1.4 \times 10^{-4}$):
1. You must have the **$3 \times 3$ position covariance matrix** $\mathbf{C}_1$ of satellite 1 and $\mathbf{C}_2$ of satellite 2 at TCA. Covariance describes the 3D ellipsoid of position uncertainty.
2. You must project the combined covariance $\mathbf{C} = \mathbf{C}_1 + \mathbf{C}_2$ onto the 2D **encounter plane** perpendicular to relative velocity (Alfano / Akella / Patera / Chan method).
3. You must integrate a 2D Gaussian probability density over the collision cross-section disk defined by the hard-body radius $R = R_1 + R_2$:
$$P_c = \frac{1}{2\pi \sigma_x \sigma_y} \iint_{\text{disk}} \exp\left( -\frac{1}{2}\left(\frac{x^2}{\sigma_x^2} + \frac{y^2}{\sigma_y^2}\right) \right) dx\,dy$$

**The Hard Truth**: Public NORAD TLEs **do not contain covariance matrices**.  
Therefore, OrbitalGuard AI enforces an honest scientific gate:
**Collision Probability is displayed as `UNAVAILABLE`**.  
The application refuses to manufacture fake covariance numbers from arbitrary constants.

---

# Section 9 ? Machine Learning Explained from Zero

### 9.1 Why Use Machine Learning in an Orbital Tracking App?
In operational space situational awareness, operators screen millions of candidate pairs daily. SGP4 propagation is fast, but evaluating thousands of steps for 50,000 objects takes computational time.
Researchers are actively exploring whether machine-learning classifiers can quickly predict whether an encounter will be hazardous using only the satellites' initial orbital elements and $t_0$ positions, without propagating the entire trajectory.

### 9.2 The Prediction Target: `below_threshold_proxy`
Because public orbital data contains zero labels of real spacecraft collisions, OrbitalGuard AI honestly defines a **proxy classification target**:
- **Target Name**: `below_threshold_proxy`
- **Definition**: $1$ if the refined SGP4 miss distance during the forecast horizon is $\le \text{threshold}$, and $0$ otherwise.
- **Honest Disclosure**: This is a proxy geometric task, **not** a collision outcome.

### 9.3 Machine Learning Pipeline Architecture
OrbitalGuard AI implements a scikit-learn classification pipeline:
$$\text{Raw Features } X \longrightarrow \text{[ SimpleImputer ]} \longrightarrow \text{[ StandardScaler ]} \longrightarrow \text{[ LogisticRegression ]} \longrightarrow \hat{y}$$

1. **`SimpleImputer(strategy='median')`**: If any orbital parameter is missing (NaN), replaces it with the median value calculated from the training partition.
2. **`StandardScaler()`**: Normalizes features to have mean 0 and variance 1: $z = (x - \mu) / \sigma$. This prevents features with large numbers (like altitude $\approx 800$ km) from dominating small features (like eccentricity $\approx 0.001$).
3. **`LogisticRegression(class_weight='balanced')`**: Models the log-odds of the positive class as a linear combination of normalized features:
$$P(Y=1|X) = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_i X_i)}}$$
`class_weight='balanced'` automatically adjusts weights inversely proportional to class frequencies to handle imbalanced datasets.

### 9.4 Feature Schema (Inputs strictly available at $t_0$)
To prevent **target leakage**, the ML pipeline only uses features available before propagation:
1. `target_inclination_deg`, `candidate_inclination_deg`, `rel_inclination_deg`
2. `target_eccentricity`, `candidate_eccentricity`
3. `target_mean_motion`, `candidate_mean_motion`, `rel_mean_motion`
4. `target_altitude_km`, `candidate_altitude_km`, `rel_altitude_km`
5. `epoch_separation_km` (miss distance at $t=0$)
6. `epoch_relative_speed_km_s` (relative speed at $t=0$)
7. `target_age_hours`, `candidate_age_hours`
8. `forecast_horizon_hours`, `sample_interval_seconds`

> **ZERO LEAKAGE**: Neither refined miss distance, nor TCA, nor relative velocity at encounter, nor satellite catalog IDs are used as predictive features.

### 9.5 The Grouped Chronological Holdout Split
A naive random row split (`train_test_split`) on orbital data is disastrous because:
If Satellite A and Satellite B have multiple observations across time, putting one in Train and another in Test allows the model to memorize the satellites' specific identities.
OrbitalGuard AI implements a **Grouped Chronological Holdout**:
1. Groups samples by `candidate_id`.
2. Deduplicates reverse pairs $(A, B)$ and $(B, A)$ using `canonical_pair_id`.
3. Ensures that all encounters involving a candidate satellite in the Test partition **never appeared anywhere in the Training or Validation partitions**.

### 9.6 Verified Model Evaluation Results
Evaluated on $N = 36$ held-out candidate groups:

| Metric | Logistic Regression | Physical Baseline ($d(t_0) \le \text{threshold}$) | Dummy Majority |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **58.33%** | 41.67% | 41.67% |
| **Precision** | **63.64%** | 50.00% | 0.00% |
| **Recall** | **66.67%** | 4.76% | 0.00% |
| **F1-Score** | **0.651** | **0.087** | **0.000** |
| **PR-AUC** | **0.649** | N/A | N/A |
| **ROC-AUC** | **0.613** | N/A | N/A |
| **Brier Score** | **0.249** | N/A | N/A |

**Interpretation**: The ML classifier outperforms the physical $t_0$ baseline by $+0.564$ in F1 score, demonstrating that relative inclination and relative altitude provide valuable predictive signal beyond simple initial distance.

---

# Section 10 ? Dashboard & UI Walkthrough

OrbitalGuard AI features a dark space-inspired Streamlit dashboard with 7 interconnected pages navigated from the sidebar.

```
Sidebar Navigation
??? 1. Mission overview
??? 2. Satellite selection
??? 3. Conjunction screening
??? 4. Orbital visualization
??? 5. Risk assessment
??? 6. ML model evaluation
??? 7. Data and system health
```

### 10.1 Page 1: Mission Overview
- **Purpose**: High-level telemetry summary of the current target satellite and latest screening run.
- **What You See**: 8 compact metric cards:
  - Target Satellite Name & NORAD Catalog ID.
  - Orbital Element Epoch & Retrieval Timestamp.
  - Number of Candidates Screened & Within-Threshold Flags.
  - Closest Encounter Distance (km) & Encounter Timestamp (UTC).
- **Behavior**: If no satellite is selected, displays a clean guidance banner directing you to the Satellite Selection page.

### 10.2 Page 2: Satellite Selection
- **Purpose**: Acquire and validate orbital data from CelesTrak, custom file upload, or offline sample.
- **Controls**:
  - `Search by name`: Enter partial name (e.g., `ISS`, `STARLINK`, `NOAA`) and click `Search name`.
  - `Search by catalog ID`: Enter 5-digit NORAD number (e.g., `25544`) and click `Search catalog ID`.
  - `Catalog group`: Select from 18 groups (`visual`, `stations`, `active`, `debris`, etc.) and click `Load catalog group`.
  - `Load bundled sample (offline)`: Loads the verified offline catalog (ISS, NOAA 15, Envisat, Vanguard 1) without internet access.
  - `Upload a TLE/3LE text file`: Drag-and-drop custom `.tle` or `.txt` element files up to 2 MB.
- **What Happens**: The validator parses checksums, displays element age, and provides a formatted metadata card and raw TLE preview.

### 10.3 Page 3: Conjunction Screening
- **Purpose**: Configure and launch the SGP4 screening engine against all loaded candidates.
- **Controls**:
  - `Forecast horizon`: Select 6, 12, 24, 48, or 72 hours.
  - `Geometric screening threshold`: Distance cutoff (0.1 to 5000 km, default 25 km).
  - `Sampling interval`: Uniform time step (30 to 600 seconds, default 60s).
  - `Maximum candidates`: Slider bounding computational load (10 to 400).
  - `Start screening`: Launches the two-stage screening engine with a live progress bar.
- **Interactive Outputs**:
  - Summary metrics: Candidates considered, propagated, skipped, failed.
  - Searchable/Sortable DataFrame: Filter by candidate name or catalog ID, and toggle "Only show within-threshold flags".
  - Candidate Detail selector: Select any candidate to inspect its exact TCA, miss distance, relative speed, and numerical refinement status.
  - Plotly Figures: Distance vs Time curve around encounter and Relative Speed vs Time plot.

### 10.4 Page 4: Orbital Visualization
- **Purpose**: Interactive 3D visualizer showing relative orbit geometry.
- **What You See**:
  - Earth scale sphere centered at the origin (TEME inertial reference).
  - Target orbit trajectory path rendered in bright cyan (`#4cc9f0`).
  - Candidate orbit trajectory path rendered in orange (`#f4a261`).
  - Pulsing encounter marker showing the exact positions at TCA.
- **Interactive Features**: Click-and-drag to rotate in 3D, scroll to zoom, hover over points to inspect Cartesian coordinates $(X, Y, Z)$ in kilometres.

### 10.5 Page 5: Risk Assessment
- **Purpose**: Deep-dive into hazard prioritization and physical probability limitations.
- **What You See**:
  - Geometric proximity banner: Minimum separation vs threshold.
  - Heuristic score card (0-100) with visual breakdown of the 70% separation, 15% velocity, and 15% freshness components.
  - **Collision Probability Banner**: Highlighted in information blue, clearly stating that $P_c$ is `UNAVAILABLE` because public TLEs lack covariance matrices.

### 10.6 Page 6: ML Model Evaluation
- **Purpose**: Audit the trained machine-learning model, validation protocol, and test metrics.
- **What You See**:
  - Model status: Artifact availability, model type (`LogisticRegression`), and target definition (`below_threshold_proxy`).
  - Grouped test set performance table comparing ML against Physical baseline and Dummy classifier.
  - Interactive Confusion Matrix Heatmap.
  - Feature Importance Bar Chart showing normalized regression coefficients.
  - Clear scientific disclosure of the single-snapshot limitation.

### 10.7 Page 7: Data and System Health
- **Purpose**: System diagnostics, data freshness monitoring, and report downloads.
- **Features**:
  - Cache status monitor: Inspect cached URL hashes, disk file sizes, and TTL expiration.
  - Diagnostic event log: Review recent application events and warnings.
  - One-click Report Download:
    - `Download Screening Report (CSV)`: Full tabular dataset of all candidate encounters.
    - `Download Full Audit Report (TXT)`: Formatted audit report including calculation settings, provenance manifests, heuristic formulas, and limitations.

---

# Section 11 ? Windows Installation and Execution Guide

Follow these exact, verified PowerShell instructions from your project folder:

### Step 1: Open PowerShell
Open Windows PowerShell and navigate to the project directory:
```powershell
cd C:\Users\DELL\orbitalguard-ai
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell shows an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again).*

### Step 3: Install Required Packages
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Run Preflight Health Check
```powershell
python scripts\run_preflight.py
```
*Expected output: All lines report `OK`, verifying dependencies, directories, and application imports.*

### Step 5: Execute Automated Test Suite
```powershell
pytest -v
```
*Expected output: `48 passed in 8.13s` (100% pass rate).*

### Step 6: Launch the Streamlit Web Application
```powershell
streamlit run app.py
```
*Expected output: Streamlit starts and opens your browser at `http://localhost:8501`.*

### Step 7: Optional CLI Data & ML Commands
```powershell
# Download live CelesTrak catalog group
python scripts\download_catalog.py --group visual

# Collect periodic historical snapshot with manifest
python scripts\collect_snapshot.py --groups stations visual

# Re-build proxy ML dataset
python -m ml.build_dataset --horizon-hours 12 --threshold-km 3000 --sample-seconds 120 --max-candidates 60

# Re-train baseline ML model
python -m ml.train_baseline

# Score an external CSV file
python -m ml.predict data\processed\proxy_dataset.csv
```

---

# Section 12 ? Testing, Quality Assurance, and Verification

### 12.1 Testing Pyramid in OrbitalGuard AI
OrbitalGuard AI implements a multi-layer testing strategy:
1. **Unit Tests**: Test individual isolated functions (e.g. `tle_checksum()`, `miss_distance()`, `local_minima_indices()`).
2. **Scientific Benchmark Tests**: Verify SGP4 propagation against official David Vallado published benchmarks (`tcppver.out` sat 5 and sat 88888).
3. **Data Pipeline Tests**: Test parsing of malformed files, duplicate handling, and checksum validation.
4. **Machine Learning Leakage Tests**: Verify grouped chronological splitting and ensure zero overlap of candidate IDs and canonical pairs across partitions.
5. **Report & Prediction Tests**: Verify CSV and TXT report generation and model loading origin security checks.
6. **Integration & UI Tests**: Headless execution of all 7 Streamlit pages and button interactions via `streamlit.testing.v1.AppTest`.

### 12.2 What Passing Tests Prove (and What They Do Not Prove)
- **What they PROVE**: The software is mathematically consistent, handles errors gracefully, correctly parses TLEs, aligns coordinate frames, avoids ML data leakage, and runs without runtime crashes.
- **What they DO NOT PROVE**: A passing test suite does **not** prove that the software can predict real-world satellite collisions. Operational accuracy is fundamentally bounded by public TLE tracking accuracy and the absence of covariance data.

---

# Section 13 ? Limitations and Future Scope

### 13.1 Current Technical Limitations
1. **Analytical Propagation (SGP4)**: SGP4 is a mean-element theory. It does not model higher-order gravity field variations (e.g., $70 \times 70$ spherical harmonics), space weather fluctuations, or atmospheric drag variations with numerical precision.
2. **Element Age Degradation**: TLE accuracy degrades rapidly over time. For LEO satellites, position error can grow by several kilometres per day.
3. **Absence of Real Collision Labels**: Public catalogs do not record real collisions. The ML pipeline is trained on proxy geometric thresholds.
4. **No Covariance in Public Data**: Without covariance matrices, operational collision probabilities ($P_c$) cannot be calculated.
5. **Catalog Truncation**: A screening run on a subset (e.g. 100 objects) does not screen the remaining 25,000+ objects in space.

### 13.2 Future Research Roadmap
1. **Long-Term Snapshot Archive**: Run `scripts/collect_snapshot.py` continuously across months to build genuine multi-epoch time series datasets.
2. **Covariance Reconstruction Models**: Research empirical covariance estimation algorithms based on historical TLE consistency.
3. **High-Fidelity Integrators**: Complement SGP4 with Cowell-method numerical integrators for high-priority conjunctions.
4. **Encounter Plane Integration**: Implement Alfano-Patera 2D probability integration modules once covariance ingestion channels become available.

---

# Section 14 ? Comprehensive Viva and Technical Interview Preparation (35 Questions)

This section provides 35 questions and answers designed specifically for college project vivas, technical reviews, and aerospace software interviews.

---

### Basic Concepts
**Q1: What is OrbitalGuard AI in one sentence?**  
*Answer:* OrbitalGuard AI is an aerospace research software tool that ingests public satellite orbital elements, propagates them forward using SGP4 in the TEME frame, detects close encounters, and provides transparent risk ranking.

**Q2: What is the difference between active satellites and space debris?**  
*Answer:* Active satellites have functioning electronics, power, communications, and thrusters that allow operators to maneuver them. Space debris consists of dead satellites, spent rocket stages, and fragments that cannot be controlled or maneuvered.

**Q3: What is a conjunction in orbital mechanics?**  
*Answer:* A conjunction is a close geometric encounter in space where two orbiting objects pass within a defined screening threshold distance of each other.

**Q4: Does detecting a conjunction mean a collision will occur?**  
*Answer:* No. A conjunction is simply a geometric close approach in a mathematical model. Because spacecraft are small (typically a few meters) and miss distances are typically several kilometres, most conjunctions pass harmlessly.

**Q5: What are the units used internally by OrbitalGuard AI?**  
*Answer:* Positions are in **kilometres (km)**, velocities are in **kilometres per second (km/s)**, angles are in **degrees ($^\circ$)**, and event times are strictly in **Coordinated Universal Time (UTC)**.

---

### Data and TLE
**Q6: What is a TLE and who produces it?**  
*Answer:* A Two-Line Element set (TLE) is a standard data format created by NORAD / US Space Force (18th Space Defense Squadron) containing mean orbital elements fitted for propagation by the SGP4 algorithm.

**Q7: What does the epoch in a TLE represent?**  
*Answer:* The epoch is the exact historical UTC timestamp at which the orbital elements were mathematically fitted from radar and optical tracking observations.

**Q8: Why does TLE data become stale?**  
*Answer:* Satellites experience unmodeled atmospheric drag fluctuations, solar activity, and gravitational anomalies. SGP4 propagation error grows as the forecast time extends further away from the element epoch.

**Q9: How does OrbitalGuard AI validate TLE records?**  
*Answer:* It validates line length (69 columns), Line 1 starting with `1 ` and Line 2 starting with `2 `, matching catalog identifiers between lines, valid UTC epoch conversions, finite numerical values, and strict modulo-10 checksum verification on columns 1-68.

**Q10: What is CelesTrak?**  
*Answer:* CelesTrak is an authoritative, freely accessible educational and research repository founded and maintained by Dr. T.S. Kelso that mirrors and distributes NORAD orbital data.

---

### Orbital Mechanics & Propagation
**Q11: What is SGP4 and why is it used instead of basic physics ($F = ma$)?**  
*Answer:* SGP4 (Simplified General Perturbations 4) is an analytical theory that incorporates Earth's equatorial bulge ($J_2$, $J_3$, $J_4$) and atmospheric drag ($B^*$). Numerical integration ($F=ma$) of millions of points is computationally slow, whereas SGP4 provides fast, standard evaluation matched to NORAD GP data.

**Q12: What is the TEME reference frame?**  
*Answer:* True Equator Mean Equinox (TEME) is an Earth-Centered Inertial (ECI) non-rotating coordinate frame whose fundamental plane is Earth's true equator and $X$-axis points to the mean equinox. It is the native output frame of SGP4.

**Q13: Why can't we compare TEME coordinates directly with GPS (ECEF) coordinates?**  
*Answer:* ECEF (Earth-Centered, Earth-Fixed) rotates with the Earth, while TEME does not. Comparing them directly without applying Greenwich Apparent Sidereal Time (GAST) would result in errors of thousands of kilometres.

**Q14: How does the two-stage conjunction screening algorithm work?**  
*Answer:* First, a coarse pass evaluates relative separation on a uniform time grid (e.g. every 60s or 120s). Second, local minima where range dips are identified. Third, SciPy's bounded scalar minimizer searches the time bracket around each minimum to locate the exact Time of Closest Approach (TCA) and true minimum separation.

**Q15: What is relative velocity and why is it important during a conjunction?**  
*Answer:* Relative velocity is $\Delta \vec{v} = \vec{v}_2 - \vec{v}_1$. Its magnitude is the closing speed (up to 15 km/s in LEO). High closing speed reduces reaction time and increases destructive kinetic energy ($E_k = \frac{1}{2}m v^2$).

---

### Risk Assessment & Collision Probability
**Q16: What is the difference between Geometric Proximity, Heuristic Score, and Collision Probability?**  
*Answer:* 
1. *Geometric Proximity*: The physical miss distance (km) and whether it crosses a user threshold.
2. *Heuristic Score*: A project-defined prioritization formula (0-100) combining separation, closing speed, and data age.
3. *Collision Probability ($P_c$)*: A rigorous statistical probability requiring covariance uncertainty matrices.

**Q17: What are the exact weights used in the project's heuristic score?**  
*Answer:* 70% separation term, 15% relative speed term (scaled to 15 km/s), and 15% data freshness term (scaled to 72 hours).

**Q18: Why does OrbitalGuard AI show Collision Probability as UNAVAILABLE?**  
*Answer:* Because public NORAD TLEs do not contain 3D position covariance matrices. Computing $P_c$ without covariance is mathematically impossible; inventing arbitrary covariance matrices would be scientifically dishonest.

**Q19: What is the encounter plane (B-plane)?**  
*Answer:* The encounter plane is a 2D plane passing through the primary object perpendicular to the relative velocity vector at TCA, upon which the combined 3D covariance ellipsoid and hard-body collision cross-section are projected.

---

### Machine Learning & Data Leakage
**Q20: Why is machine learning used if SGP4 already calculates distances?**  
*Answer:* SGP4 requires propagating hundreds of time steps for each pair. ML explores whether initial orbital geometry at $t_0$ can rapidly filter or prioritize hazardous pairs before full numerical screening.

**Q21: What is the exact prediction target of the ML model?**  
*Answer:* `below_threshold_proxy`: a binary label ($1$ if the refined SGP4 miss distance is $\le$ threshold, $0$ otherwise). It is an honest geometric proxy, not an actual collision label.

**Q22: What is data leakage and how was it prevented in this project?**  
*Answer:* Data leakage occurs when test data or future outcome information accidentally contaminates training features. It was prevented by:
1. Excluding refined miss distance, TCA, and encounter speed from input features.
2. Implementing Grouped Chronological Holdout (grouping by candidate ID so test satellites never appear in training).
3. Deduplicating reverse pairs $(A, B)$ and $(B, A)$ via canonical pair IDs `(min(id1, id2), max(id1, id2))`.
4. Fitting the imputer and scaler strictly on the training partition only.

**Q23: What ML model architecture is implemented?**  
*Answer:* A scikit-learn pipeline consisting of `SimpleImputer(strategy='median')`, `StandardScaler()`, and `LogisticRegression(class_weight='balanced')`.

**Q24: What is the test set size and what were the verified results?**  
*Answer:* The test set contains 36 held-out pairs. Logistic Regression achieved Accuracy 58.33%, Precision 63.64%, Recall 66.67%, and F1-score 0.651, outperforming the static $t_0$ physical baseline (F1 0.087) by $+0.564$.

**Q25: Why is Accuracy a misleading metric for rare event prediction?**  
*Answer:* If 99% of encounters are non-hazardous, a dummy classifier that always predicts "0" achieves 99% accuracy while detecting zero hazards. Precision, Recall, F1, and PR-AUC are far more meaningful.

**Q26: What is the Brier score?**  
*Answer:* The Brier score measures the mean squared difference between predicted probabilities and actual binary outcomes: $\frac{1}{N} \sum (\hat{p}_i - y_i)^2$. Lower is better (0.0 is perfect calibration). OrbitalGuard AI achieved 0.249.

---

### Software Engineering & Architecture
**Q27: Why use Streamlit instead of a separate React/FastAPI stack?**  
*Answer:* Streamlit runs directly in Python, sharing in-memory data structures with SGP4, NumPy, and scikit-learn without JSON serialization overhead, latency, or complex multi-server deployment.

**Q28: How does the application maintain responsiveness during large screenings?**  
*Answer:* It uses a coarse screening margin ($4 \times$ threshold), vectorized NumPy batch distance calculations, interactive progress updates, and user-configurable candidate bounds (default 80, max 400).

**Q29: How does the application handle offline operation?**  
*Answer:* It includes a validated local offline catalog (`sample_catalog.tle`) with ISS, NOAA 15, Envisat, and Vanguard 1, allowing full demonstration without network connectivity.

**Q30: How are model artifacts protected against tampering?**  
*Answer:* `ModelPredictionService` validates metadata fields, feature schemas, and checks that `trusted_origin == 'orbitalguard-ai-local'`, refusing to load foreign or incompatible models.

---

### Practical Demonstration & Viva Tips
**Q31: How do you demonstrate the complete project in a 3-minute viva presentation?**  
*Answer:*
1. Start Streamlit (`streamlit run app.py`).
2. Go to **Satellite selection** and click **Load bundled sample (offline)**. Show ISS selected and explain its TLE parameters and checksum.
3. Go to **Conjunction screening**, set threshold to 5000 km, horizon to 12h, and click **Start screening**. Show the progress bar.
4. Show the sorted candidate table, select an encounter, and show the miss-distance time curve.
5. Go to **Orbital visualization** and rotate the interactive 3D Earth and orbit paths.
6. Go to **Risk assessment** and explain why Heuristic Score is 78/100 while Collision Probability is honestly gated as UNAVAILABLE.
7. Go to **ML model evaluation** and explain the proxy target, grouped holdout, and confusion matrix.
8. Go to **Data and system health** and download the CSV/TXT audit report.

**Q32: What will you answer if the examiner asks: "Can this predict a real satellite crash next week?"**  
*Answer:* "No, sir/ma'am. SGP4 propagation from public TLEs provides relative geometric trajectory screening. Real collision prediction requires high-accuracy covariance matrices and attitude data that are classified or proprietary and absent from public catalogs."

**Q33: What is the single-snapshot limitation in the ML pipeline?**  
*Answer:* Because the dataset was constructed from a single catalog retrieval, all satellite epochs originate from the same day. While grouped splitting prevents satellite identity leakage, true temporal evaluation requires snapshots collected across weeks or months.

**Q34: How did you fix the SGP4 reference test error during development?**  
*Answer:* The test was named `test_vanguard_sgp4_at_epoch`, but its assertions had been copied from Space-Track Report No. 3 benchmark sat 88888. I checked David Vallado's official benchmark output (`tcppver.out`), corrected the coordinates for sat 5 to `[7022.465, -1400.083, 0.040]` km, and added a dedicated test for sat 88888.

**Q35: What would be your first improvement if given 6 more months?**  
*Answer:* Run `scripts/collect_snapshot.py` on an automated cron schedule to build a genuine 6-month historical time-series archive, implement covariance estimation heuristics from TLE consistency, and integrate Cowell-method numerical propagation for high-priority conjunctions.

---

# Section 15 ? Glossary and Quick Revision Sheet

### Alphabetical Glossary
- **$B^*$ (B-Star)**: An empirical drag parameter used by SGP4 representing atmospheric resistance in units of inverse Earth radii ($R_\oplus^{-1}$).
- **B-Plane (Encounter Plane)**: A 2D plane perpendicular to the relative velocity vector at TCA used for collision probability calculations.
- **Canonical Pair ID**: A unique identifier for a satellite interaction sorted by catalog IDs: `f"{min(id1, id2)}_{max(id1, id2)}"`, preventing reverse duplicate pairs.
- **Conjunction**: A close approach encounter between two orbiting objects in space.
- **Covariance Matrix**: A $3 \times 3$ symmetric matrix describing positional uncertainty (standard deviations $\sigma_x, \sigma_y, \sigma_z$ and cross-correlations) around a satellite.
- **Eccentricity ($e$)**: A dimensionless number from 0 to 1 describing the elongation of an ellipse ($0 = \text{circle}$).
- **Epoch**: The specific UTC timestamp at which an orbital element set was fitted.
- **Geostationary Orbit (GEO)**: A circular orbit at an altitude of $\approx 35,786$ km where an orbital period matches Earth's rotation (24 hours).
- **Inclination ($i$)**: The tilt of an orbital plane relative to Earth's equator in degrees.
- **Kessler Syndrome**: A theoretical scenario proposed by NASA scientist Donald Kessler where the density of space debris in LEO becomes high enough that collisions cause a cascading chain reaction.
- **Low Earth Orbit (LEO)**: Orbits with altitudes between $\approx 160$ km and $2,000$ km.
- **Mean Motion ($n$)**: The average angular speed of a satellite in revolutions per day.
- **Miss Distance ($d$)**: The Euclidean distance $\|\Delta \vec{r}\|$ between two satellites at closest approach.
- **NORAD Catalog ID**: A unique sequential 5-digit number assigned to every tracked artificial space object.
- **$P_c$ (Collision Probability)**: The mathematical probability of two objects colliding during an encounter.
- **RAAN ($\Omega$)**: Right Ascension of the Ascending Node: the angle in degrees from the Vernal Equinox to the ascending node.
- **Relative Velocity ($\Delta \vec{v}$)**: Vector velocity difference between candidate and target: $\vec{v}_2 - \vec{v}_1$.
- **SGP4**: Simplified General Perturbations 4 analytical orbital propagation model.
- **TCA**: Time of Closest Approach: the exact UTC second when separation distance reaches its local minimum.
- **TEME**: True Equator Mean Equinox Earth-Centered Inertial coordinate reference frame.
- **TLE**: Two-Line Element set: standardized 69-character 2-line format for orbital elements.

### Five Golden Rules for Your Viva
1. **Never say "the AI predicts collisions"**. Say: *"The ML model classifies a proxy geometric proximity label."*
2. **Never say "this is operational NASA software"**. Say: *"This is an academic research prototype demonstrating close-approach screening and risk gating."*
3. **Always emphasize covariance**: Explain that public TLEs lack covariance, which is why collision probability is responsibly gated as UNAVAILABLE.
4. **Know the 70/15/15 heuristic weights**: 70% separation, 15% relative speed, 15% element freshness.
5. **Remember the reference frame**: SGP4 outputs are strictly in **TEME (True Equator Mean Equinox)** in **kilometres** and **km/s**.
