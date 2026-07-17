"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : standardized_preview.py

Description :
Milestone 3 - Phase 1: preview of the standardized dataset.
Displays the clean business-field DataFrames produced by the
StandardizationService along with any cleaning warnings.
=============================================================================
"""

import streamlit as st

from components.header import page_header
from components.footer import page_footer

from services.standardization_service import StandardizationService


ENTITY_ICONS = {

    "Sales": "🧾",

    "Products": "📦",

    "Stores": "🏬",

    "Inventory": "🏭",

    "Calendar": "📅",

    "Customers": "👥",

    "Promotions": "🏷",

    "Suppliers": "🚚"

}


def standardized_preview():

    page_header(

        "🧪 Standardized Preview",

        "Clean business-field view consumed by forecasting "

        "and inventory optimization."

    )

    if st.button("← Back to Dataset"):

        st.session_state.current_page = "dataset_details"

        st.rerun()

    dataset_id = st.session_state.get("selected_dataset_id")

    if dataset_id is None:

        st.warning("No dataset selected.")

        return

    try:

        report = StandardizationService.load_with_report(
            dataset_id
        )

    except Exception as error:

        st.error(f"Standardization failed: {error}")

        return

    st.subheader(f"📁 {report['dataset_name']}")

    frames = report["frames"]

    if not frames:

        st.warning(

            "No standardized data available. Map columns for at "

            "least one file first."

        )

        page_footer()

        return

    # ---------------------------------------------------------
    # Summary metrics
    # ---------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric("Entities", len(frames))

    c2.metric(

        "Total Rows",

        f"{sum(len(frame) for frame in frames.values()):,}"

    )

    c3.metric("Warnings", len(report["warnings"]))

    # ---------------------------------------------------------
    # Warnings
    # ---------------------------------------------------------

    if report["warnings"]:

        with st.expander(

                f"⚠ Cleaning Warnings ({len(report['warnings'])})"

        ):

            for warning in report["warnings"]:

                st.write(f"- {warning}")

    # ---------------------------------------------------------
    # One tab per standardized entity
    # ---------------------------------------------------------

    tabs = st.tabs([

        f"{ENTITY_ICONS.get(entity, '📄')} {entity}"

        for entity in frames

    ])

    for tab, (entity, frame) in zip(tabs, frames.items()):

        with tab:

            a, b = st.columns(2)

            a.metric("Rows", f"{len(frame):,}")

            b.metric("Business Fields", len(frame.columns))

            st.dataframe(

                frame.head(50),

                use_container_width=True

            )

            st.caption(

                "Showing first 50 rows. Datatypes: "

                + ", ".join(

                    f"{column} ({dtype})"

                    for column, dtype

                    in frame.dtypes.astype(str).items()

                )

            )

    page_footer()
