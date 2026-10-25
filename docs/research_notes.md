# Research notes

These notes record the physical and catalog assumptions used in OrbitalGuard AI. They are not operational procedures.

## TLE / GP element sets

NORAD two-line element sets encode mean orbital elements fitted for the SGP4/SDP4 general-perturbations propagator (Hoots & Roehrich; Vallado et al.). CelesTrak documents the GP query interface (`gp.php?{QUERY}=VALUE`) and `FORMAT=TLE` so checksums on columns 1–68 can be verified (Kelso). A TLE is **not** an osculating Cartesian state. The epoch in line 1 (two-digit year + day-of-year) is the element epoch, not a tracking observation time.

Checksum: sum of all digits in columns 1–68 plus 1 for each minus sign, modulo 10.

## SGP4

SGP4/SDP4 is an analytic mean-element propagator consistent with those GP fits. python-sgp4 implements the Vallado/Revisiting Spacetrack Report #3 formulation and returns position/velocity in **TEME** kilometres and kilometres per second. It is not a high-fidelity numerical force model (no estimated drag weather, no solid Earth tides as a fitted OD, no covariance). Error typically grows with **element age** and **propagation span**; kilometre-class errors within a day are possible for low-Earth objects with poorly modelled drag.

## Frames

- **TEME**: True Equator, Mean Equinox — Earth-centred, non-rotating as used by SGP4. Not identical to GCRS/J2000.
- **ECI / GCRS**: inertial frames used in many high-fidelity tools; converting TEME to GCRS needs documented bias/nutation conventions this prototype does not apply.
- **ITRF / ECEF**: Earth-fixed; required for ground tracks. This app does not rotate TEME into ECEF, so plots are inertial geometry, not maps over Earth.

Mixing frames without a documented transformation would silently corrupt miss distance. The code therefore compares SGP4 states only in TEME.

## Close approach vs collision

Minimum of `|r₂ − r₁|` is a **geometric miss distance**. Collision would additionally require object size, attitude, and a statistical treatment of uncertainty. Public TLEs do not include 6×6 (or relative) covariance, so encounter-plane Pc methods (Alfano, Chan, Patera, and related NASA CARA practice) are **not** computable from this data. OrbitalGuard AI refuses to invent covariance.

## Catalog coverage

CelesTrak public GP groups are incomplete relative to the full space object catalog. Debris, classified objects, and recently manoeuvred satellites may be absent. A screening over `GROUP=stations` does not bound risk from other groups. Cache hits are labelled `from_cache` so stale records are never presented as live.

## Stale-element policy

There is no single certified TLE age cutoff. This project warns when element age exceeds 48 hours **or** half the requested forecast horizon. Users must still treat SGP4 geometry as approximate.

## Machine learning

A genuine collision-labelled, multi-epoch dataset is not shipped. The optional pipeline builds `below_threshold_proxy` from SGP4 of a snapshot. That task can only approximate screening, and a single snapshot cannot provide true future-event validation. Grouped splits on candidate catalog ID prevent the same object from sitting in train and test; timestamps on one snapshot still do not create a future window.

## Space-debris context

ESA and NASA publish debris-environment overviews and conjunction-assessment concepts. Operational collision avoidance uses owner/operator ephemerides, special perturbations, and covariance — not TLE screening alone. This repository is a research dashboard on public GP data.
