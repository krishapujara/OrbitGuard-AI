from __future__ import annotations

import streamlit as st

from backend.data_sources import DataSourceService
from config.settings import get_settings
from frontend.pages import (
    conjunction_screening,
    model_evaluation,
    orbital_visualization,
    overview,
    risk_assessment,
    satellite_selection,
    system_health,
)

CSS = """
<style>
.stApp { background-color: #070b14; color: #d7e3f4; }
section[data-testid="stSidebar"] { background-color: #0c1322; }
h1, h2, h3 { color: #e8eef7; letter-spacing: 0.02em; }
div[data-testid="stMetricValue"] { color: #4cc9f0; }
.block-container { padding-top: 1.2rem; }
</style>
"""

PAGES = {
    "Mission overview": overview.render,
    "Satellite selection": satellite_selection.render,
    "Conjunction screening": conjunction_screening.render,
    "Orbital visualization": orbital_visualization.render,
    "Risk assessment": risk_assessment.render,
    "ML model evaluation": model_evaluation.render,
    "Data and system health": system_health.render,
}


def run() -> None:
    settings = get_settings()
    st.set_page_config(page_title=settings.app_name, layout="wide", page_icon="🛰️")
    st.markdown(CSS, unsafe_allow_html=True)
    if "data_source" not in st.session_state:
        st.session_state["data_source"] = DataSourceService(settings)
    st.sidebar.title(settings.app_name)
    st.sidebar.caption(
        "Research prototype — geometric screening, not certified collision avoidance. "
        "Offline path: Satellite selection → Load bundled sample."
    )
    page = st.sidebar.radio("Navigate", list(PAGES.keys()))
    st.sidebar.markdown(
        f"Version `{settings.app_version}`  \nCoordinate frame: **TEME**  \nUnits: **km**, **km/s**"
    )
    st.title(settings.app_name)
    st.caption("Space Debris Proximity Forecasting and Collision Risk Engine")
    PAGES[page]()
