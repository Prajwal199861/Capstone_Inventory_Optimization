"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : products.py

Description :
Milestone 4 - Phase 2: Product Intelligence (Product 360 Dashboard).

A single screen combining Product Master Data, Current Inventory,
Forecast Demand, Inventory Risk, AI Insights and Historical Trends
for one product - so a manager never has to navigate across the
Forecast/Inventory/AI pages to answer "should I reorder this?".

No business logic lives here. Everything is computed by
ProductService, which itself only aggregates the existing
DemandService / ForecastService / InventoryService / AIRecommendation
Service outputs - forecasting, optimization and the AI call only ever
run when the user explicitly triggers them (batch forecast on the
Forecast page, and the "Generate AI Insight" button below).
=============================================================================
"""

import streamlit as st
import plotly.graph_objects as go

from components.header import page_header
from components.footer import page_footer
from components.metric_card import metric_card
from components.ai_insight_panel import render_ai_insight_panel

from services.demand_service import DemandService
from services.product_service import ProductService


RISK_BADGE = {

    "Critical": "🔴",

    "High": "🟠",

    "Medium": "🟡",

    "Low": "🟢"

}


@st.cache_data(ttl=300, show_spinner=False)
def _load_bundle(
        dataset_id: int
):
    """
    The one expensive pass (standardized data + batch forecast join +
    reorder/risk calculations, via ProductService.load_dataset) per
    dataset, cached across every rerun this page triggers (typing in
    the search box, selecting a product, expanding a section) so
    those reruns never re-trigger it.
    """

    return ProductService.load_dataset(dataset_id)


def _format_value(
        value,
        prefix: str = "",
        suffix: str = ""
) -> str:

    if value is None:

        return "n/a"

    try:

        if value != value:  # NaN

            return "n/a"

    except TypeError:

        pass

    if isinstance(value, (int, float)):

        return f"{prefix}{value:,.2f}{suffix}"

    return f"{prefix}{value}{suffix}"


def _product_table_section(
        bundle: dict
):
    """Requirements 1-3: searchable, sortable product table. Returns
    the selected Product ID, or None when nothing is selected."""

    products = ProductService.list_products(bundle)

    if products.empty:

        st.info("No products found for this dataset.")

        return None

    search = st.text_input(
        "🔍 Search Product (Name or ID)",
        key="product_search"
    )

    if search:

        term = search.strip()

        mask = (

            products["Product ID"]

            .astype(str)

            .str.contains(term, case=False, na=False)

        ) | (

            products["Product Name"]

            .astype(str)

            .str.contains(term, case=False, na=False)

        )

        filtered = products[mask]

    else:

        filtered = products

    st.caption(
        f"Showing {len(filtered):,} of {len(products):,} product(s). "

        f"Click a row to view its full profile."
    )

    display = filtered.copy()

    display["Risk Level"] = display["Risk Level"].map(

        lambda level: f"{RISK_BADGE.get(level, '')} {level}"

    )

    selection = st.dataframe(

        display,

        use_container_width=True,

        hide_index=True,

        on_select="rerun",

        selection_mode="single-row"

    )

    selected_positions = selection.selection.rows

    if not selected_positions:

        return None

    return filtered.iloc[selected_positions[0]]["Product ID"]


def _product_info_card(
        product: dict
):

    with st.container(border=True):

        st.markdown("**📦 Product Information**")

        st.write(f"**{product['Product Name']}**  ({product['Product ID']})")

        st.write(f"Category: {_format_value(product['Category'])}")

        st.write(f"Season: {_format_value(product['Season'])}")

        st.write(f"Price: {_format_value(product['Price'], prefix='$')}")

        m1, m2 = st.columns(2)

        with m1:

            metric_card("Current Stock", _format_value(
                product["Current Stock"]
            ))

            metric_card("Safety Stock", _format_value(
                product["Safety Stock"]
            ))

            metric_card("Reorder Point", _format_value(
                product["Reorder Point"]
            ))

        with m2:

            metric_card("Forecast Demand", _format_value(
                product["Forecast Demand"]
            ))

            metric_card("Recommended Qty", _format_value(
                product["Recommended Quantity"]
            ))

            metric_card(
                "Risk",
                f"{RISK_BADGE.get(product['Risk Level'], '')} "
                f"{product['Risk Level']}"
            )

        st.caption(f"Status: {product['Status']}")


def _forecast_summary_card(
        forecast: dict | None
):

    with st.container(border=True):

        st.markdown("**📈 Forecast Summary**")

        if forecast is None:

            st.info("Forecast not available for this product.")

            return

        metric_card("Demand (Horizon Total)", _format_value(
            forecast["total"]
        ))

        st.write(
            f"Forecast Horizon: {forecast['horizon']} "

            f"{forecast['granularity'].lower()} period(s)"
        )

        st.write(f"Forecast Model: {forecast['model_name']}")

        if (

                forecast["lower_total"] is not None

                and forecast["upper_total"] is not None

        ):

            st.write(

                f"Confidence Interval: "

                f"{forecast['lower_total']:,.0f} - "

                f"{forecast['upper_total']:,.0f}"

            )

        st.caption(
            f"Run: {forecast['created_at']:%Y-%m-%d %H:%M}"
        )


def _inventory_summary_card(
        product: dict
):

    with st.container(border=True):

        st.markdown("**🏭 Inventory Summary**")

        if product["Stock Basis"] == "Assumed":

            st.caption(
                "⚠ No Current Stock data uploaded - shown values "
                "assume a healthy operating level."
            )

        elif product["Stock Basis"] == "Mixed":

            st.caption(
                "⚠ Some store(s) have no Current Stock data - their "
                "figures assume a healthy operating level."
            )

        metric_card("Current Stock", _format_value(
            product["Current Stock"]
        ))

        metric_card("Safety Stock", _format_value(
            product["Safety Stock"]
        ))

        metric_card("Reorder Point", _format_value(
            product["Reorder Point"]
        ))

        metric_card("Inventory Value", _format_value(
            product["Inventory Value"], prefix="$"
        ))

        metric_card(
            "Days Remaining",
            _format_value(product["Days Remaining"])
        )


def _store_availability(
        stores
):

    st.markdown("**🏬 Store Availability**")

    if len(stores) == 1 and stores.iloc[0]["Store ID"] == "All Stores":

        st.caption("This dataset has no per-store inventory data.")

        st.write(
            f"All Stores - Stock: "

            f"{_format_value(stores.iloc[0]['Current Stock'])}"
        )

        return

    display = stores[

        ["Store ID", "Current Stock", "Risk Level", "Status"]

    ].copy()

    display["Risk Level"] = display["Risk Level"].map(

        lambda level: f"{RISK_BADGE.get(level, '')} {level}"

    )

    st.dataframe(display, use_container_width=True, hide_index=True)


def _historical_forecast_chart(
        history,
        forecast: dict | None
):

    st.markdown("**Historical Demand vs Forecast**")

    if history is None and forecast is None:

        st.info("No historical or forecast data available.")

        return

    figure = go.Figure()

    if history is not None:

        measure = history.columns[0]

        figure.add_trace(

            go.Scatter(

                x=history.index,

                y=history[measure],

                mode="lines",

                name="Historical",

                line=dict(color="#1565C0")

            )

        )

    if forecast is not None:

        points = forecast["points"]

        if points["Lower"].notna().all() and points["Upper"].notna().all():

            figure.add_trace(

                go.Scatter(

                    x=points["Period"],

                    y=points["Upper"],

                    mode="lines",

                    line=dict(width=0),

                    showlegend=False,

                    hoverinfo="skip"

                )

            )

            figure.add_trace(

                go.Scatter(

                    x=points["Period"],

                    y=points["Lower"],

                    mode="lines",

                    line=dict(width=0),

                    fill="tonexty",

                    fillcolor="rgba(38, 166, 154, 0.2)",

                    name="Confidence Band"

                )

            )

        figure.add_trace(

            go.Scatter(

                x=points["Period"],

                y=points["Forecast"],

                mode="lines",

                name="Forecast",

                line=dict(color="#26A69A", dash="dash")

            )

        )

    figure.update_layout(

        margin=dict(l=10, r=10, t=30, b=10),

        height=360

    )

    st.plotly_chart(figure, use_container_width=True)


def _inventory_position_chart(
        product: dict
):

    st.markdown("**Inventory Position**")

    labels = [

        "Current Stock",

        "Safety Stock",

        "Reorder Point",

        "Recommended Qty"

    ]

    values = [

        product["Current Stock"],

        product["Safety Stock"],

        product["Reorder Point"],

        product["Recommended Quantity"]

    ]

    figure = go.Figure(

        go.Bar(

            x=labels,

            y=values,

            marker_color=["#1565C0", "#26A69A", "#F9A825", "#E53935"]

        )

    )

    figure.update_layout(

        margin=dict(l=10, r=10, t=30, b=10),

        height=360,

        yaxis_title="Units"

    )

    st.plotly_chart(figure, use_container_width=True)


def _recommendation_card(
        product: dict
):

    st.markdown("**✅ Recommendation**")

    badge = RISK_BADGE.get(product["Risk Level"], "")

    alert = {

        "Critical": st.error,

        "High": st.warning,

        "Medium": st.warning,

        "Low": st.success

    }.get(product["Risk Level"], st.info)

    alert(

        f"{badge} **{product['Status']}** ({product['Risk Level']} risk) "

        f"- {product['Reason']}"
    )

    c1, c2 = st.columns(2)

    with c1:

        metric_card(
            "Recommended Quantity",
            _format_value(product["Recommended Quantity"])
        )

    with c2:

        metric_card(
            "Days Remaining",
            _format_value(product["Days Remaining"])
        )


def _ai_insight_row(
        product: dict
) -> dict:
    """Maps the aggregated product dict to the exact keys
    AIRecommendationService.build_payload() reads (the same shape as
    an InventoryService recommendation row) - reusing the existing
    prompt/service, per the handover requirement."""

    return {

        "Product Name": product["Product Name"],

        "Category": product["Category"],

        "Season": product["Season"],

        "Store ID": product["Store ID"],

        "Forecast Demand": product["Forecast Demand"],

        "Demand Change %": product["Demand Change %"],

        "Current Stock": product["Current Stock"],

        "Stock Basis": product["Stock Basis"],

        "Target Stock Level": product["Target Stock Level"],

        "Recommended Quantity": product["Recommended Quantity"],

        "Days Remaining": product["Days Remaining"],

        "Status": product["Status"],

        "Risk Level": product["Risk Level"]

    }


def _product_detail_section(
        dataset_id: int,
        bundle: dict,
        product_id: str
):

    try:

        detail = ProductService.get_product_detail(

            bundle,

            dataset_id,

            product_id

        )

    except ValueError as error:

        st.warning(str(error))

        return

    product = detail["product"]

    st.divider()

    st.subheader(f"📦 {product['Product Name']}")

    c1, c2, c3 = st.columns(3)

    with c1:

        _product_info_card(product)

    with c2:

        _forecast_summary_card(detail["forecast"])

    with c3:

        _inventory_summary_card(product)

    _store_availability(detail["stores"])

    for note in detail["notes"]:

        st.caption(f"ℹ {note}")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

        _historical_forecast_chart(detail["history"], detail["forecast"])

    with c2:

        _inventory_position_chart(product)

    st.divider()

    _recommendation_card(product)

    st.divider()

    cache_key = (

        dataset_id,

        product_id,

        str(product["Recommendation Timestamp"])

    )

    label = (

        f"**{product['Product Name']}** ({product['Store ID']}) - "

        f"{product['Status']}, {product['Risk Level']} risk."
    )

    render_ai_insight_panel(

        cache_key,

        _ai_insight_row(product),

        label,

        empty_message=""

    )


def products():

    page_header(

        "📦 Products",

        "Product 360 - forecast, inventory, risk and AI insight for "
        "one product, in one place."

    )

    datasets = DemandService.get_ready_datasets()

    if not datasets:

        st.info(

            "No READY datasets found. Upload a dataset and complete "

            "its column mapping first."

        )

        page_footer()

        return

    dataset_labels = {

        f"{dataset.dataset_name} (id {dataset.id})": dataset.id

        for dataset in datasets

    }

    selected = st.selectbox("Dataset", list(dataset_labels.keys()))

    dataset_id = dataset_labels[selected]

    try:

        bundle = _load_bundle(dataset_id)

    except ValueError as error:

        st.warning(str(error))

        page_footer()

        return

    for note in bundle["notes"]:

        st.caption(f"ℹ {note}")

    product_id = _product_table_section(bundle)

    if product_id is not None:

        _product_detail_section(dataset_id, bundle, product_id)

    page_footer()
