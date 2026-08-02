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

from ai.config import SECTION_LABELS
from ai.recommendation import AIRecommendationService

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

        "Category",

        "Store ID",

        "Current Stock",

        "Stock Basis",

        "Forecast Demand",

        "Demand Change %",

        "Safety Stock",

        "Reorder Point",

        "Recommended Quantity",

        "Days Remaining",

        "Risk Level",

        "Status",

        "Reason"

    ]

    selection = st.dataframe(

        filtered[display_columns],

        use_container_width=True,

        hide_index=True,

        on_select="rerun",

        selection_mode="single-row"

    )

    _ai_insight_section(dataset_id, filtered, selection)

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


def _insight_cache_key(
        dataset_id: int,
        row
) -> tuple:
    """
    Identifies one product's insight across reruns/products so
    switching row selection never shows a stale/mismatched insight,
    and a previously generated one doesn't need regenerating (a paid
    API call) just because Streamlit rerun.
    """

    return (

        dataset_id,

        row["Product ID"],

        row["Store ID"],

        str(row["Recommendation Timestamp"])

    )


def _render_insight(
        insight: dict
):

    for key, label in SECTION_LABELS.items():

        st.markdown(f"**{label}**")

        st.write(insight[key] or "_Not provided by the model._")

    caption_bits = [f"{insight['word_count']} words"]

    if insight["over_word_limit"]:

        caption_bits.append("⚠ over the 250-word guideline")

    if insight["missing_sections"]:

        caption_bits.append(
            "missing: " + ", ".join(insight["missing_sections"])
        )

    st.caption(" · ".join(caption_bits))


def _ai_insight_section(
        dataset_id: int,
        filtered,
        selection
):
    """
    Phase 8: contextual per-product AI insight for whichever row the
    user selects in the table above - generated on demand (a live API
    call) and cached in session_state so it survives reruns without
    being regenerated for every widget interaction on the page.
    """

    st.divider()

    st.subheader("🤖 AI Insight")

    selected_positions = selection.selection.rows

    if not selected_positions:

        st.caption(
            "Select a product row in the table above, then generate "
            "a business-friendly AI insight for it."
        )

        return

    row = filtered.iloc[selected_positions[0]]

    cache_key = _insight_cache_key(dataset_id, row)

    st.write(
        f"Selected: **{row['Product Name']}** "
        f"({row['Store ID']}) - {row['Status']}, "
        f"{row['Risk Level']} risk."
    )

    generate = st.button("🤖 Generate AI Insight")

    insights = st.session_state.setdefault("ai_insights", {})

    if generate:

        try:

            with st.spinner("Generating AI insight..."):

                insights[cache_key] = {

                    "ok": True,

                    "data": AIRecommendationService.generate(
                        row.to_dict()
                    )

                }

        except ValueError as error:

            insights[cache_key] = {"ok": False, "error": str(error)}

    cached = insights.get(cache_key)

    if cached is None:

        return

    if cached["ok"]:

        _render_insight(cached["data"])

    else:

        st.error(cached["error"])
