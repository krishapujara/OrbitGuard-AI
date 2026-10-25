"""CSV and text report export with provenance and limitations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backend.exceptions import ReportError
from backend.models import ScreeningRun
from config.settings import get_settings


class ReportService:
    def to_dataframe(self, run: ScreeningRun) -> pd.DataFrame:
        rows = []
        for a in run.approaches:
            rows.append(
                {
                    "record_kind": "propagated_prediction",
                    "target_name": a.target_name,
                    "target_id": a.target_id,
                    "candidate_name": a.candidate_name,
                    "candidate_id": a.candidate_id,
                    "target_epoch_utc": a.target_epoch_utc.isoformat(),
                    "candidate_epoch_utc": a.candidate_epoch_utc.isoformat(),
                    "tca_utc": a.tca_utc.isoformat(),
                    "min_separation_km": a.min_separation_km,
                    "relative_velocity_km_s": a.relative_velocity_km_s,
                    "threshold_km": a.screening_threshold_km,
                    "within_threshold": a.within_threshold,
                    "screening_status": a.screening_status,
                    "refinement_status": a.refinement_status,
                    "heuristic_score": a.heuristic_score,
                    "ml_proxy_score": a.ml_proxy_score,
                    "ml_proxy_label": a.ml_proxy_label,
                    "collision_probability_status": a.collision_probability_status,
                    "collision_probability": a.collision_probability,
                    "target_age_hours": a.target_age_hours,
                    "candidate_age_hours": a.candidate_age_hours,
                    "horizon_hours": a.forecast_horizon_hours,
                    "sample_interval_seconds": a.sample_interval_seconds,
                    "coordinate_frame": "TEME",
                }
            )
        return pd.DataFrame(rows)

    def export_csv(self, run: ScreeningRun, path: Path | None = None) -> Path:
        settings = get_settings()
        path = path or settings.data_processed / f"screening_{_stamp()}.csv"
        try:
            df = self.to_dataframe(run)
            df.to_csv(path, index=False)
        except OSError as exc:
            raise ReportError(f"Could not write CSV report: {exc}") from exc
        return path

    def export_text(self, run: ScreeningRun, path: Path | None = None) -> Path:
        settings = get_settings()
        path = path or settings.data_processed / f"screening_{_stamp()}.txt"
        target = run.target
        lines = [
            "OrbitalGuard AI — conjunction screening report",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "Record kinds: orbital elements are observed GP/TLE records; approaches are propagated predictions.",
            "",
            "TARGET",
            f"  name: {target.name}",
            f"  catalog_id: {target.catalog_id}",
            f"  epoch_utc: {target.epoch_utc.isoformat()}",
            f"  retrieved_at: {target.retrieved_at.isoformat()}",
            f"  source: {target.source}",
            f"  source_url: {target.source_url}",
            f"  from_cache: {target.from_cache}",
            f"  validation: {target.validation_status}",
            "",
            "SETTINGS",
            f"  forecast_horizon_hours: {run.horizon_hours}",
            f"  threshold_km: {run.threshold_km}",
            f"  sample_interval_seconds: {run.sample_interval_seconds}",
            f"  catalog_group: {run.catalog_group}",
            "",
            "COVERAGE",
            f"  objects_considered: {run.objects_considered}",
            f"  objects_propagated: {run.objects_propagated}",
            f"  objects_skipped: {run.objects_skipped}",
            f"  objects_failed: {run.objects_failed}",
            f"  close_approach_rows: {len(run.approaches)}",
        ]
        for note in run.coverage_notes:
            lines.append(f"  note: {note}")
        lines.append("")
        lines.append("RESULTS (propagated predictions)")
        if not run.approaches:
            lines.append("  No candidate approaches were recorded for this run.")
        for a in run.approaches[:50]:
            lines.append(
                f"  {a.candidate_name} ({a.candidate_id}) TCA={a.tca_utc.isoformat()} "
                f"min_sep={a.min_separation_km:.3f} km v_rel={a.relative_velocity_km_s:.3f} km/s "
                f"status={a.screening_status} score={a.heuristic_score}"
            )
        lines.extend(
            [
                "",
                "RISK SCORING METHODOLOGY",
                "  Heuristic score (0-100) = 100 * [0.70 * (1 - sep/threshold) + 0.15 * (v_rel/15 km/s) + 0.15 * (1 - max_age/72 h)]",
                "  Scores are transparent ranking aids prioritizing geometric proximity, not physical collision probabilities.",
                "  Statistical collision probability (Pc) remains explicitly UNAVAILABLE due to lack of covariance in public TLEs.",
                "",
                "ASSUMPTIONS AND LIMITATIONS",
                "  SGP4 TEME geometry only; not an operational conjunction assessment.",
                "  Geometric close approach is not a collision.",
                "  Statistical collision probability is unavailable without covariance.",
                "  Heuristic scores are ranking aids, not probabilities.",
                "  Public catalogs are incomplete and delayed relative to classified tracking.",
            ]
        )
        try:
            path.write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            raise ReportError(f"Could not write text report: {exc}") from exc
        return path


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
