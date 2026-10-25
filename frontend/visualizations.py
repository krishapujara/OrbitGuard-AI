"""Plotly charts. All trajectory vectors are SGP4 TEME kilometres."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.models import ApproachResult, OrbitalRecord
from backend.orbital_propagation import OrbitalPropagationService
from config.settings import get_settings

CYAN = "#4cc9f0"
ORANGE = "#f4a261"
WHITE = "#e8eef7"
NAVY = "#070b14"


def earth_sphere(radius_km: float, n: int = 24) -> go.Surface:
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    x = radius_km * np.outer(np.cos(u), np.sin(v))
    y = radius_km * np.outer(np.sin(u), np.sin(v))
    z = radius_km * np.outer(np.ones_like(u), np.cos(v))
    return go.Surface(
        x=x,
        y=y,
        z=z,
        opacity=0.35,
        showscale=False,
        colorscale=[[0, "#123055"], [1, "#1b4f72"]],
        name="Earth (geometric sphere)",
        hoverinfo="skip",
    )


def orbit_figure(
    target: OrbitalRecord,
    candidate: OrbitalRecord | None,
    times: list[datetime],
    approach: ApproachResult | None = None,
    selected_time: datetime | None = None,
) -> go.Figure:
    settings = get_settings()
    prop = OrbitalPropagationService()
    step = max(1, len(times) // settings.max_plot_points)
    plot_times = times[::step]
    fig = go.Figure()
    fig.add_trace(earth_sphere(settings.mean_earth_radius_km))
    tr, _, _, t_ok = prop.propagate_many(target, plot_times)
    fig.add_trace(
        go.Scatter3d(
            x=tr[:, 0],
            y=tr[:, 1],
            z=tr[:, 2],
            mode="lines",
            line={"color": CYAN, "width": 4},
            name=f"Target {target.name} (SGP4 TEME)",
        )
    )
    if candidate is not None:
        cr, _, _, _ = prop.propagate_many(candidate, plot_times)
        fig.add_trace(
            go.Scatter3d(
                x=cr[:, 0],
                y=cr[:, 1],
                z=cr[:, 2],
                mode="lines",
                line={"color": ORANGE, "width": 4},
                name=f"Candidate {candidate.name} (SGP4 TEME)",
            )
        )
    if approach is not None:
        s1 = prop.propagate(target, approach.tca_utc)
        fig.add_trace(
            go.Scatter3d(
                x=[s1.position_km[0]],
                y=[s1.position_km[1]],
                z=[s1.position_km[2]],
                mode="markers",
                marker={"size": 7, "color": "#ff6b6b"},
                name=f"Target at TCA ({approach.tca_utc.isoformat()})",
            )
        )
        if candidate is not None:
            s2 = prop.propagate(candidate, approach.tca_utc)
            fig.add_trace(
                go.Scatter3d(
                    x=[s2.position_km[0]],
                    y=[s2.position_km[1]],
                    z=[s2.position_km[2]],
                    mode="markers",
                    marker={"size": 7, "color": "#ffd166"},
                    name="Candidate at TCA",
                )
            )
    if selected_time is not None:
        stt = prop.propagate(target, selected_time)
        fig.add_trace(
            go.Scatter3d(
                x=[stt.position_km[0]],
                y=[stt.position_km[1]],
                z=[stt.position_km[2]],
                mode="markers",
                marker={"size": 6, "color": CYAN},
                name="Target at selected time",
            )
        )
        if candidate is not None:
            stc = prop.propagate(candidate, selected_time)
            fig.add_trace(
                go.Scatter3d(
                    x=[stc.position_km[0]],
                    y=[stc.position_km[1]],
                    z=[stc.position_km[2]],
                    mode="markers",
                    marker={"size": 6, "color": ORANGE},
                    name="Candidate at selected time",
                )
            )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=NAVY,
        scene=dict(
            xaxis_title="X TEME (km)",
            yaxis_title="Y TEME (km)",
            zaxis_title="Z TEME (km)",
            aspectmode="data",
        ),
        legend=dict(orientation="h"),
        margin=dict(l=0, r=0, t=30, b=0),
        title="Propagated TEME trajectories (not measured ephemerides)",
    )
    return fig


def separation_figure(times: list[datetime], distances_km: list[float], tca: datetime | None = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=times,
            y=distances_km,
            mode="lines",
            name="|r2-r1| (km, TEME)",
            line={"color": CYAN},
        )
    )
    if tca is not None:
        fig.add_shape(
            type="line",
            x0=tca,
            x1=tca,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color=ORANGE, dash="dash"),
        )
        fig.add_annotation(
            x=tca,
            y=1,
            yref="paper",
            text="TCA",
            showarrow=False,
            font=dict(color=ORANGE),
        )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=NAVY,
        xaxis_title="UTC",
        yaxis_title="Separation (km)",
        title="Relative separation versus time (propagated)",
    )
    return fig


def relative_velocity_figure(times: list[datetime], speeds: list[float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=speeds, mode="lines", name="|v2-v1| (km/s)", line={"color": ORANGE}))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=NAVY,
        xaxis_title="UTC",
        yaxis_title="Relative speed (km/s)",
        title="Relative velocity magnitude versus time (propagated)",
    )
    return fig


def separation_distribution(values: list[float], threshold: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=values, nbinsx=30, name="min separation (km)", marker_color=CYAN))
    fig.add_vline(x=threshold, line_dash="dash", line_color=ORANGE, annotation_text="threshold")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=NAVY,
        xaxis_title="Minimum separation (km)",
        yaxis_title="Count",
        title="Screening-distance distribution",
    )
    return fig


def confusion_heatmap(matrix: list[list[int]]) -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=["pred 0", "pred 1"],
            y=["true 0", "true 1"],
            colorscale="Blues",
            text=matrix,
            texttemplate="%{text}",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=NAVY,
        title="Confusion matrix (proxy labels, not collisions)",
    )
    return fig


def coefficient_bar(items: list[dict]) -> go.Figure:
    names = [i["feature"] for i in items]
    vals = [i["coefficient"] for i in items]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=CYAN))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=NAVY,
        title="Logistic regression coefficients (training-set scale)",
        yaxis=dict(autorange="reversed"),
    )
    return fig
