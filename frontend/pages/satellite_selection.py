from __future__ import annotations

import streamlit as st

from backend.data_sources import DataSourceService
from backend.exceptions import DataSourceError, ObjectNotFoundError, OrbitalGuardError
from backend.tle_parser import records_by_query
from config.settings import get_settings
from frontend.components import record_preview


def render() -> None:
    st.header("Satellite selection")
    st.caption("Public GP/TLE records are fetched from CelesTrak. Missing objects are not substituted.")
    settings = get_settings()
    service: DataSourceService = st.session_state["data_source"]
    group = st.selectbox("Catalog group", settings.catalog_groups, index=0)
    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        name_q = st.text_input("Search by name", placeholder="ISS, NOAA 15, ...")
        search_name = st.button("Search name")
    with col_b:
        cat_q = st.text_input("Search by catalog ID", placeholder="25544")
        search_cat = st.button("Search catalog ID")
    with col_c:
        refresh = st.button("Refresh data", use_container_width=True)
        load_group = st.button("Load catalog group", type="primary")
        load_sample = st.button("Load bundled sample (offline)", use_container_width=True)

    load_error = None
    records = st.session_state.get("catalog_records") or []
    try:
        if load_sample:
            sample_path = settings.project_root / "data" / "sample_metadata" / "sample_catalog.tle"
            if not sample_path.exists():
                st.error("Bundled sample catalog is missing from data/sample_metadata.")
            else:
                parsed, issues = service.parse_upload(sample_path.read_text(encoding="utf-8"), sample_path.name)
                records = parsed
                st.session_state["catalog_records"] = records
                st.session_state["catalog_group"] = "bundled-sample"
                st.info(
                    f"Loaded {len(parsed)} historical sample TLEs. Epochs are from 2000/2019, not live catalog data."
                )
                if issues:
                    st.warning(f"{len(issues)} validation issues in the bundled sample.")
        if load_group or refresh:
            with st.spinner("Requesting CelesTrak GP data..."):
                records = service.fetch_group(group, refresh=refresh)
                st.session_state["catalog_records"] = records
                st.session_state["catalog_group"] = group
        if search_name:
            if not name_q.strip():
                st.warning("Enter a name before searching.")
            else:
                with st.spinner("Searching CelesTrak by name..."):
                    found = service.search_by_name(name_q, refresh=refresh)
                if not found:
                    st.warning(f"No CelesTrak GP records matched NAME={name_q!r}. No substitute was selected.")
                else:
                    records = found
                    st.session_state["catalog_records"] = records
        if search_cat:
            if not cat_q.strip():
                st.warning("Enter a catalog identifier before searching.")
            else:
                with st.spinner("Searching CelesTrak by catalog ID..."):
                    found = service.search_by_catalog_id(cat_q, refresh=refresh)
                records = found
                st.session_state["catalog_records"] = records
    except ObjectNotFoundError as exc:
        load_error = str(exc)
        st.error(str(exc))
    except DataSourceError as exc:
        load_error = str(exc)
        st.error(str(exc))
        cached = st.session_state.get("catalog_records") or []
        if cached:
            st.warning("Showing previously loaded records. They may be cached or stale; check from_cache and epoch.")
            records = cached
    except OrbitalGuardError as exc:
        load_error = str(exc)
        st.error(str(exc))

    uploaded = st.file_uploader("Upload a TLE/3LE text file", type=["txt", "tle", "3le"])
    if uploaded is not None:
        if uploaded.size > settings.max_upload_bytes:
            st.error("Upload exceeds the 2 MB size limit.")
        else:
            try:
                text = uploaded.getvalue().decode("utf-8", errors="replace")
                parsed, issues = service.parse_upload(text, uploaded.name)
                st.session_state["catalog_records"] = parsed
                records = parsed
                st.success(f"Parsed {len(parsed)} records from {uploaded.name}.")
                if issues:
                    st.warning(f"{len(issues)} validation issues in the upload.")
                    st.dataframe(issues, use_container_width=True)
            except OrbitalGuardError as exc:
                st.error(str(exc))

    records = st.session_state.get("catalog_records") or records
    st.session_state["last_data_error"] = load_error
    if not records:
        st.info("Load a catalog group, search CelesTrak, or upload a TLE file.")
        return

    filter_q = st.text_input("Filter loaded records", "")
    filtered = records_by_query(records, filter_q) if filter_q else records
    options = [f"{r.catalog_id} | {r.name}" for r in filtered]
    if not options:
        st.warning("No loaded records match that filter. The requested object was not substituted.")
        return
    choice = st.selectbox("Select target satellite", options)
    target = filtered[options.index(choice)]
    st.session_state["target"] = target
    cache_note = "This record was served from the local cache." if target.from_cache else "This record came from a live request or upload."
    st.caption(cache_note)
    record_preview(target)
