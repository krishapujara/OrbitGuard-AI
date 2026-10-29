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

    group = st.selectbox(
        "Catalog group",
        settings.catalog_groups,
        index=0,
        help="Select an orbital constellation, satellite fleet, or debris field from CelesTrak.",
    )

    col_a, col_b, col_c = st.columns([2, 2, 2])
    with col_a:
        name_q = st.text_input(
            "Search by name",
            placeholder="ISS, NOAA 15, ...",
            autocomplete="off",
            help="Search CelesTrak by satellite name string.",
        )
        search_name = st.button("Search name", use_container_width=True)
    with col_b:
        cat_q = st.text_input(
            "Search by catalog ID",
            placeholder="25544",
            autocomplete="off",
            help="Search CelesTrak by 5-digit NORAD catalog number.",
        )
        search_cat = st.button("Search catalog ID", use_container_width=True)
    with col_c:
        refresh = st.button(
            "Refresh data",
            use_container_width=True,
            help="Bypasses local cache and downloads fresh live GP data from CelesTrak.",
        )
        load_group = st.button(
            "Load catalog group",
            type="primary",
            use_container_width=True,
            help="Fetches all satellites in the selected group (e.g. 16 space stations, 156 visual satellites, or debris) to populate the target list and screening candidates.",
        )
        load_sample = st.button(
            "Load bundled sample (offline)",
            use_container_width=True,
            help="Loads 4 verified historical satellites (ISS, NOAA 15, Iridium, Cosmos) for 100% offline demonstration.",
        )

    st.caption(
        "?? **What does 'Load catalog group' do?** It queries CelesTrak (or reads local cache) for all satellites belonging to the chosen group (e.g. `stations`, `visual`, `debris`) so you can pick a target satellite and screen it against the entire group for close encounters."
    )

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
                if records:
                    st.session_state["target"] = records[0]
                st.session_state["last_data_error"] = None
                st.success(
                    f"? **Loaded {len(parsed)} historical sample TLEs (offline catalog).** "
                    f"Selected target: **{records[0].name} ({records[0].catalog_id})**."
                )
                st.toast(f"Loaded {len(parsed)} offline sample satellites!")
                if issues:
                    st.warning(f"{len(issues)} validation issues in the bundled sample.")

        if load_group or refresh:
            with st.spinner(f"Requesting '{group}' GP data from CelesTrak..."):
                records = service.fetch_group(group, refresh=refresh)
                st.session_state["catalog_records"] = records
                st.session_state["catalog_group"] = group
                st.session_state["last_data_error"] = None
                if records:
                    st.session_state["target"] = records[0]

                origin = "local cache" if (records and records[0].from_cache) else "live CelesTrak GP API"
                retrieved_str = records[0].retrieved_at.strftime("%Y-%m-%d %H:%M UTC") if records else ""

                if refresh:
                    st.success(
                        f"?? **Refreshed {len(records)} satellites** for group **'{group.upper()}'** directly from CelesTrak!"
                    )
                else:
                    st.success(
                        f"? **Successfully loaded {len(records)} satellites** from catalog group **'{group.upper()}'** (Source: {origin}, retrieved: {retrieved_str}).\n\n"
                        f"?? **Target satellite**: Automatically set to **{records[0].name} ({records[0].catalog_id})**. You can choose a different satellite in the dropdown below, or go to **Conjunction screening** to analyze collision risks!"
                    )
                st.toast(f"Loaded {len(records)} satellites for '{group}'!")

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
                    st.session_state["target"] = found[0]
                    st.session_state["last_data_error"] = None
                    st.success(
                        f"?? **Found {len(found)} record(s)** matching '{name_q}'. Set target to **{found[0].name} ({found[0].catalog_id})**!"
                    )
                    st.toast(f"Found {len(found)} satellites matching '{name_q}'")

        if search_cat:
            if not cat_q.strip():
                st.warning("Enter a catalog identifier before searching.")
            else:
                with st.spinner("Searching CelesTrak by catalog ID..."):
                    found = service.search_by_catalog_id(cat_q, refresh=refresh)
                records = found
                st.session_state["catalog_records"] = records
                st.session_state["target"] = found[0]
                st.session_state["last_data_error"] = None
                st.success(
                    f"?? **Found satellite {cat_q} ({found[0].name})**! Set as target below."
                )
                st.toast(f"Loaded satellite {cat_q}")

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
        else:
            offline_snap = service.find_offline_snapshot(group)
            with st.container():
                st.markdown("#### ??? Offline & Fallback Options")
                st.info(
                    "Cloud deployments (such as Streamlit Community Cloud) can encounter rate-limits "
                    "or timeouts when connecting to CelesTrak. You can load an offline snapshot or the bundled "
                    "sample catalog to test all screening, propagation, visualization, and risk features uninterrupted."
                )
                bcol1, bcol2 = st.columns(2)
                if offline_snap:
                    if bcol1.button(f"Load offline {group} snapshot", use_container_width=True, type="secondary"):
                        parsed, issues = service.load_offline_snapshot(offline_snap)
                        st.session_state["catalog_records"] = parsed
                        st.session_state["catalog_group"] = group
                        if parsed:
                            st.session_state["target"] = parsed[0]
                        st.session_state["last_data_error"] = None
                        st.success(f"Loaded {len(parsed)} offline records ({offline_snap['description']}).")
                        st.rerun()
                if bcol2.button("Load bundled sample catalog", use_container_width=True, key="err_fallback_sample"):
                    sample_path = settings.project_root / "data" / "sample_metadata" / "sample_catalog.tle"
                    if sample_path.exists():
                        parsed, issues = service.parse_upload(sample_path.read_text(encoding="utf-8"), sample_path.name)
                        st.session_state["catalog_records"] = parsed
                        st.session_state["catalog_group"] = "bundled-sample"
                        if parsed:
                            st.session_state["target"] = parsed[0]
                        st.session_state["last_data_error"] = None
                        st.success(f"Loaded {len(parsed)} historical sample TLEs.")
                        st.rerun()
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
                if parsed:
                    st.session_state["target"] = parsed[0]
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

    filter_q = st.text_input("Filter loaded records", "", autocomplete="off", help="Filter satellites in this catalog by name or ID.")
    filtered = records_by_query(records, filter_q) if filter_q else records
    options = [f"{r.catalog_id} | {r.name}" for r in filtered]
    if not options:
        st.warning("No loaded records match that filter. The requested object was not substituted.")
        return

    # Determine default selection index based on current target if present
    default_idx = 0
    current_target = st.session_state.get("target")
    if current_target is not None:
        target_label = f"{current_target.catalog_id} | {current_target.name}"
        if target_label in options:
            default_idx = options.index(target_label)

    choice = st.selectbox("Select target satellite", options, index=default_idx)
    target = filtered[options.index(choice)]
    st.session_state["target"] = target
    cache_note = "This record was served from the local cache." if target.from_cache else "This record came from a live request or upload."
    st.caption(cache_note)

    # Next steps guidance card
    st.info(
        f"?? **Target satellite '{target.name}' ({target.catalog_id}) is active!**\n\n"
        "?? Next step: Open **Conjunction screening** from the sidebar to forecast close approaches, compute miss distances, and assess collision risks!"
    )

    record_preview(target)
