# OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-54%20Passed-brightgreen.svg)]()
[![Propagator](https://img.shields.io/badge/Propagator-SGP4%20TEME-informational.svg)]()
[![Framework](https://img.shields.io/badge/UI-Streamlit-red.svg)]()
[![Deployment](https://img.shields.io/badge/Live%20App-orbitguardai.streamlit.app-brightgreen.svg)](https://orbitguardai.streamlit.app/)

Research prototype space situational awareness application for relative orbital geometry forecasting, conjunction screening, proximity risk prioritization, and defensible proxy machine-learning evaluation using public NORAD General Perturbations (GP) Two-Line Element (TLE) records.

**Public Live Deployment**: [https://orbitguardai.streamlit.app/](https://orbitguardai.streamlit.app/)

> **CRITICAL SCIENTIFIC & SAFETY NOTICE**  
> OrbitalGuard AI is an academic and research engineering prototype. It is **not** a certified operational collision-avoidance system.  
> 1. A predicted geometric close approach is **not** an actual collision.  
> 2. Public TLE records do not contain state covariance matrices; therefore, **statistical collision probability ($P_c$) is physically unavailable and is explicitly gated as such**. Arbitrary covariance matrices are never manufactured.  
> 3. Heuristic screening scores (0-100) are interpretable geometric ranking aids based on 70% separation, 15% relative speed, and 15% element freshness?not physical probabilities or certified aerospace safety standards.  
> 4. Machine learning models predict a proxy geometric label (`below_threshold_proxy`) and do not predict physical collision events.

---

## Complete Project Documentation Suite

| Document | Purpose |
| :--- | :--- |
| **[Project Help & Examiner Guide](docs/PROJECT_HELP.md)** | **Quick 3-minute viva presentation walkthrough, step-by-step demo, and examiner defense FAQ.** |
| **[Debugging & Audit Report](docs/DEBUGGING_AND_AUDIT_REPORT.md)** | **Root cause analysis and resolution of CelesTrak timeouts, /api/v2/user/details 404s, and console warnings.** |
| **[UI Test Matrix](docs/UI_TEST_MATRIX.md)** | **Exhaustive audit matrix of every button, slider, input, chart, and expander across all 7 pages.** |
| **[API & Architecture Audit](docs/API_AUDIT_REPORT.md)** | **Detailed API audit report covering service contracts, CelesTrak endpoints, and security posture.** |
| **[Test Execution Report](docs/TEST_REPORT.md)** | **Full pytest execution log: 54 passed tests across 11 test modules with benchmark verification.** |
| **[Orbital Mechanics Validation](docs/ORBITAL_VALIDATION_REPORT.md)** | **SGP4 propagation, TEME coordinate frames, Vallado sat 5 & 88888 benchmarks, and $P_c$ gating.** |
| **[Feature Status Matrix](docs/FEATURE_STATUS.md)** | **Complete status matrix of all implemented features, offline pathways, and provenance tracking.** |
| **[Deployment & Operations Guide](docs/DEPLOYMENT.md)** | **Streamlit Community Cloud deployment instructions, cloud NAT handling, and environment settings.** |
| **[Beginner's Technical Guide](docs/BEGINNER_GUIDE.md)** | **Comprehensive 15-section guide covering astrodynamics, ML pipeline, architecture, and 35 viva questions.** |
| **[Feature Gap Analysis](docs/FEATURE_GAP_ANALYSIS.md)** | Stated objectives vs actual capabilities, gap analysis, and implemented enhancements. |
| **[Architecture Guide](docs/architecture.md)** | System components, module structure, and data flow diagrams. |
| **[Model Card](docs/model_card.md)** | ML model architecture, features, grouped holdout split, and test metrics ($N=36$). |

---

## 7 Interactive Dashboard Pages

1. **Mission Overview**: Executive summary cards, target satellite status, screening results summary, and SGP4 propagation failure breakdown.
2. **Satellite Selection**: Live CelesTrak catalog fetching (with custom User-Agent, split timeouts, and offline snapshot fallbacks), 100% offline bundled historical sample (ISS, NOAA 15, Iridium, Cosmos), name/ID search, and 2 MB TLE/3LE upload validation.
3. **Conjunction Screening**: Two-stage SGP4 screening (uniform coarse grid + SciPy Brent numerical refinement) with candidate filtering, miss distance plots, and relative speed curves.
4. **Orbital Visualization**: Interactive WebGL 3D orbit viewer in the inertial TEME reference frame with reference Earth sphere and step-by-step propagation time slider.
5. **Risk Assessment**: Clear 3-tier risk evaluation separating Geometric Proximity, Heuristic Score (70/15/15 weights), and strictly gated Statistical Collision Probability ($P_c$).
6. **ML Model Evaluation**: Evaluation of the `below_threshold_proxy` scikit-learn pipeline with confusion matrix, feature coefficients, and comparison against physical and majority baselines.
7. **Data and System Health**: Diagnostic ping, SHA-256 catalog cache provenance inspector, and 1-click export of CSV and TXT encounter reports.

---

## Installation & Execution (Windows PowerShell)

```powershell
# 1. Clone repository and navigate to workspace
cd E:\orbitalguard-ai

# 2. (Optional) Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run system preflight checks
python scripts/run_preflight.py

# 5. Run full automated test suite (54 tests)
pytest -v

# 6. Launch interactive Streamlit application
streamlit run app.py
```

---

## Offline Demonstration Path (Zero Network Required)

1. Open the dashboard at `http://localhost:8501` or [orbitguardai.streamlit.app](https://orbitguardai.streamlit.app/).
2. Navigate to **Satellite selection**.
3. Click **Load bundled sample (offline)**.
4. Select **25544 \| ISS (ZARYA)** as the target.
5. Navigate to **Conjunction screening** and click **Start screening**.
6. Explore **Orbital visualization**, **Risk assessment**, and **Data and system health**.
