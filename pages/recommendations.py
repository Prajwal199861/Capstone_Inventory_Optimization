"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : recommendations.py

Description :
Milestone 3 - Phase 3: renders the inventory recommendations table -
Store/Product/Risk filters, the detail grid and the CSV export button.

Not a routed page on its own; imported by pages/inventory_dashboard.py
so the detail-table concern can evolve (e.g. pagination, a dedicated
"Recommendations" nav entry) without touching the KPI/run workflow.
=============================================================================
"""

import streamlit as st

from services.inventory_service import InventoryService

ALL_OPTION = "All"


def render_recommendations(
        dataset_id: int,
        recommendations
):
    """Filter controls + detail table + export for one run's output."""

    st.subheader("Recommendations")

    if recommendations.empty:

        st.info("No recommendations for the current selection.")

        return

    f1, f2, f3 = st.columns(3)

    with f1:

        stores = [ALL_OPTION] + sorted(
            recommendations["Store ID"].dropna().unique().tolist()
        )

        store_filter = st.selectbox("Store", stores)

    with f2:

        products = [ALL_OPTION] + sorted(
            recommendations["Product Name"].dropna().unique().tolist()
        )

        product_filter = st.selectbox("Product", products)

    with f3:

        risk_filter = st.selectbox(

            "Risk Level",

            [ALL_OPTION, "Critical", "High", "Medium", "Low"]

        )

    filtered = recommendations

    if store_filter != ALL_OPTION:

        filtered = filtered[filtered["Store ID"] == store_filter]

    if product_filter != ALL_OPTION:

        filtered = filtered[
            filtered["Product Name"] == product_filter
        ]

    if risk_filter != ALL_OPTION:

        filtered = filtered[filtered["Risk Level"] == risk_filter]

    st.caption(
        f"Showing {len(filtered):,} of {len(recommendations):,} "
        f"recommendation(s)."
    )

    display_columns = [

        "Product ID",

        "Product Name",

        "Store ID",

        "Current Stock",

        "Stock Basis",

        "Forecast Demand",

        "Safety Stock",

        "Reorder Point",

        "Recommended Quantity",

        "Days Remaining",

        "Risk Level",

        "Status",

        "Reason"

    ]

    st.dataframe(

        filtered[display_columns],

        use_container_width=True,

        hide_index=True

    )

    e1, e2 = st.columns([1, 3])

    with e1:

        st.download_button(

            "⬇ Download CSV",

            filtered.to_csv(index=False).encode("utf-8"),

            file_name=f"inventory_recommendations_dataset_{dataset_id}.csv",

            mime="text/csv",

            use_container_width=True

        )

    with e2:

        if st.button("💾 Save Export to Server", use_container_width=True):

            path = InventoryService.export_csv(dataset_id, filtered)

            st.success(f"Saved to {path}")
