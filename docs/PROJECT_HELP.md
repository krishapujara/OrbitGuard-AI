# OrbitalGuard AI ? Project Help, Demonstration & Examiner Guide

**Project**: OrbitalGuard AI ? Space Debris Proximity Forecasting & Collision Risk Engine  
**Document**: `docs/PROJECT_HELP.md`  
**Target Audience**: Students, Aerospace Software Evaluators, Viva Examiners, and Developers  

---

## 1. Quick Demonstration Workflow (3-Minute Viva Presentation)

If you are presenting OrbitalGuard AI in a college viva, project review, or technical evaluation, follow this structured, battle-tested demonstration path:

```
[Start Dashboard]
       ?
       ?
[Page 2: Satellite Selection] ??> Click "Load bundled sample (offline)"
       ?                          (Loads historical ISS, NOAA 15, Iridium, Cosmos)
       ?
[Page 3: Conjunction Screening] ??> Set Horizon: 24h, Threshold: 25 km, Sample: 60s
       ?                            Click "Start screening"
       ?
[Review Encounter Results] ??> Show refined TCA, min separation (km), relative velocity
       ?                       Show Plotly separation curve and velocity-over-time plots
       ?
[Page 4: Orbital Visualization] ??> Show 3D TEME orbits, step time slider, explain inertial frame
       ?
       ?
[Page 5: Risk Assessment] ??> Explain the 3 Tiers:
       ?                      1. Geometric proximity (miss distance vs threshold)
       ?                      2. Heuristic screening score (70/15/15 weights)
       ?                      3. Statistical Pc: STRICTLY GATED as unavailable (explain why!)
       ?
[Page 6: ML Model Evaluation] ??> Explain below_threshold_proxy target, data leakage prevention
       ?                          via canonical pair deduplication, and held-out test metrics
       ?
[Page 7: System Health] ??> Click "Export CSV and text report" and download results
```

---

## 2. Step-by-Step Feature Walkthrough

### Step 1: Launch the Application
- **Cloud**: Navigate to [https://orbitguardai.streamlit.app/](https://orbitguardai.streamlit.app/)
- **Local**: Open PowerShell in `E:\orbitalguard-ai` and run:
  ```powershell
  streamlit run app.py
  ```

### Step 2: Satellite Selection
1. Open **Satellite selection** from the left navigation bar.
2. Click **Load bundled sample (offline)**.
   - *Examiner Explanation*: "We load a verified 4-object historical catalog containing the International Space Station, NOAA 15, Iridium 33 debris, and Cosmos 2251 debris. This enables 100% reproducible offline screening independent of external network availability."
3. Select **25544 | ISS (ZARYA)** as the primary target satellite.
4. Review the element epoch, retrieved timestamp, and checksum validation status.

### Step 3: Conjunction Screening
1. Navigate to **Conjunction screening**.
2. Configure settings:
   - **Forecast horizon**: 24 hours (time forward from epoch).
   - **Screening threshold**: 25.0 km (geometric boundary).
   - **Sampling interval**: 60 seconds (coarse uniform grid).
3. Click **Start screening**.
4. Review the results:
   - **Coarse Grid vs. Refined TCA**: Point out that the coarse grid detects candidates, but continuous minimization (Brent's method) refines the exact sub-second Time of Closest Approach (TCA) and true minimum separation.
   - **Interactive Plots**: Select a candidate from the dropdown to display the miss distance curve and relative speed curve around TCA.

### Step 4: Orbital Visualization
1. Navigate to **Orbital visualization**.
2. Examine the 3D trajectory plot:
   - Explain that all coordinates are represented in the **TEME frame** (True Equator, Mean Equinox) in kilometres.
   - Clarify that the Earth sphere has radius $R_E = 6378.137\text{ km}$ and serves as a geometric scale reference in the inertial frame.
3. Drag the **Time index slider** to watch the satellites propagate along their orbital trajectories.

### Step 5: Risk Assessment (Critical Viva Section!)
1. Navigate to **Risk assessment**.
2. Clearly explain the **Three Distinct Concepts**:
   - **Concept 1 ? Geometric Proximity**: SGP4 predicted miss distance ($d_{\min}$), TCA, and relative velocity.
   - **Concept 2 ? Heuristic Screening Score**: A transparent ranking metric (0 to 100) combining 70% miss distance, 15% relative speed, and 15% element freshness. Clearly state: *"This is a ranking aid, NOT a physical collision probability."*
   - **Concept 3 ? Statistical Collision Probability ($P_c$):** Point to the **"unavailable"** badge. Explain: *"Public TLEs lack positional error covariance matrices. Calculating a probability without genuine covariance requires fabricating numbers, which is scientifically dishonest. OrbitalGuard AI responsibly gates $P_c$ as unavailable."*

### Step 6: ML Model Evaluation
1. Navigate to **ML model evaluation**.
2. Explain the ML engineering methodology:
   - **Target**: `below_threshold_proxy` (predicts whether SGP4 refined miss distance $\le 25\text{ km}$).
   - **Data Leakage Control**: Highlight that canonical pair tracking:
     $$\text{pair\_key} = (\min(\text{id}_1, \text{id}_2), \max(\text{id}_1, \text{id}_2))$$
     was implemented to prevent reverse-pair leakage between train and test splits.
   - **Pipeline**: `SimpleImputer` -> `StandardScaler` -> `LogisticRegression`.
   - **Metrics**: Grounded on a held-out test set ($N=36$): ML model achieves F1 0.651, significantly outperforming the naive physical epoch-threshold baseline (F1 0.087).

### Step 7: System Health & Report Export
1. Navigate to **Data and system health**.
2. Click **Export CSV and text report**.
3. Download the generated CSV and TXT files to demonstrate that all screening calculations, provenance hashes, and risk breakdowns can be exported for operational archiving.

---

## 3. Frequently Asked Questions (Viva / Examiner Defense)

### Q1: Why does the system report that Collision Probability ($P_c$) is unavailable?
**Answer**: Computing a mathematically valid collision probability requires integrating a 2D Gaussian probability density function over the encounter collision cross-section. This integral requires the $3\times 3$ positional error covariance matrices of both objects at TCA. Public CelesTrak TLEs are mean elements and contain zero covariance data. Manufacturing an arbitrary covariance matrix produces meaningless numbers. Therefore, OrbitalGuard AI responsibly reports $P_c$ as unavailable.

### Q2: What is the difference between SGP4 and numerical orbital integration?
**Answer**: SGP4 is an analytical perturbation propagator based on Brouwer-Lyddane theory. It evaluates closed-form mathematical equations for secular and periodic gravitational ($J_2, J_3, J_4$) and atmospheric drag perturbations. It is fast and compatible with TLEs. Numerical integration (such as Cowell's method or Encke's method) numerically integrates high-order differential equations of motion, requiring accurate initial state vectors and complex force models (e.g. high-order gravity fields, solar radiation pressure, atmospheric models).

### Q3: What is the TEME coordinate frame and why is it used?
**Answer**: TEME stands for True Equator, Mean Equinox. It is the non-standard, quasi-inertial celestial reference frame defined by the US Space Command specifically for SGP4 theory. Because SGP4 outputs Cartesian coordinates directly in TEME, all relative distance and velocity calculations must remain in TEME. Comparing TEME coordinates with Earth-fixed ECEF coordinates without polar motion and sidereal time transformations would produce errors of thousands of kilometres.

### Q4: Why did CelesTrak requests time out on Streamlit Community Cloud?
**Answer**: Streamlit Community Cloud applications share public outbound NAT IP addresses on AWS EC2. CelesTrak's Cloudflare firewall actively throttles or drops connections from datacenter IP pools when queried with generic `python-requests` headers. OrbitalGuard AI resolves this by using an identifiable User-Agent header, bounded connect/read timeouts (6s/20s), and automatic fallback to pre-packaged disk snapshots.

### Q5: What exactly does your Machine Learning model predict?
**Answer**: The ML model predicts `below_threshold_proxy`: a binary indicator of whether a candidate pair's propagated SGP4 miss distance will fall inside the user's geometric screening threshold. It is an astrodynamic proxy classification task designed to evaluate whether orbital state features can screen close approaches quickly. It does NOT predict physical collision outcomes or satellite destruction.
