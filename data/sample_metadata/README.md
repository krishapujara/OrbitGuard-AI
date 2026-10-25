# Bundled sample catalog

These four two-line element sets are **historical public TLEs** used for offline
demo and tests. They are not live catalog snapshots.

| Name | Catalog ID | Epoch (UTC, TLE) | Role |
| --- | --- | --- | --- |
| ISS (ZARYA) | 25544 | 2019-12-09 (day 343.69339541) | Example from python-sgp4 documentation |
| HST | 20580 | 2019-12-09 | Geometric screening candidate |
| NOAA 15 | 25338 | 2019-12-09 | Polar LEO candidate |
| VANGUARD 1 | 5 | 2000-06-27 (Vallado example) | SGP4 reference object |

Checksum digits were recomputed with the NORAD modulo-10 rule on columns 1–68.
Do not treat these epochs as current; element age will be large relative to today.
Use **Refresh data** / CelesTrak for operational-looking freshness, or run
`python scripts/download_catalog.py`.
