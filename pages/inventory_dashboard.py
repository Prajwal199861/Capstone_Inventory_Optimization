"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : inventory_dashboard.py

Description :
Milestone 3 - Phase 3: Inventory Optimization dashboard.

Workflow: select a READY dataset -> load its latest batch forecast ->
run inventory optimization -> view summary KPIs -> filter by
Store/Product/Risk -> export recommendations. No business logic lives
here; everything is computed by InventoryService / InventoryMetrics.
=============================================================================
"""

import streamlit as st

from components.header import page_header
from components.footer import page_footer
from components.metric_card import metric_card

from config import (
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_OVERSTOCK_FACTOR,
    DEFAULT_REVIEW_PERIOD_DAYS,
    DEFAULT_SERVICE_LEVEL,
    SERVICE_LEVEL_Z_SCORES
)

from services.demand_service import DemandService
from services.forecast_service import ForecastService
from services.inventory_service import InventoryService

from utils.inventory_metrics import InventoryMetrics

from pages.recommendations import render_recommendations


def _settings_controls():
    """Configurable optimization parameters (Required Inputs: Lead
    Time and Safety Stock are configurable per the handover spec)."""

    with st.expander("⚙ Optimization Settings", expanded=False):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            lead_time_days = st.number_input(

                "Default Lead Time (days)",

                min_value=1,

                value=DEFAULT_LEAD_TIME_DAYS,

                help=(

                    "Used when a product's Inventory record has no "

                    "'Lead Time' mapped."

                )

            )

        with c2:

            review_period_days = st.number_input(

                "Review Period (days)",

                min_value=1,

                value=DEFAULT_REVIEW_PERIOD_DAYS,

                help="How often stock is reviewed and reordered."

            )

        with c3:

            service_level = st.selectbox(

                "Service Level",

                sorted(SERVICE_LEVEL_Z_SCORES.keys()),

                index=sorted(SERVICE_LEVEL_Z_SCORES.keys()).index(
                    DEFAULT_SERVICE_LEVEL
                ),

                format_func=lambda value: f"{value:.0%}",

                help="Target probability of not stocking out."

            )

        with c4:

            overstock_factor = st.number_input(

                "Overstock Factor (x demand)",

                min_value=1.0,

                value=DEFAULT_OVERSTOCK_FACTOR,

                step=0.5,

                help=(

                    "Stock above this multiple of forecast demand is "

                    "flagged as overstock."

                )

            )

    return {

        "lead_time_days": float(lead_time_days),

        "review_period_days": float(review_period_days),

        "service_level": float(service_level),

        "overstock_factor": float(overstock_factor)

    }


def _run_params(dataset_id: int, settings: dict) -> dict:
    """Identity of the current run so a stored result is only shown
    while it still matches (dataset switch never shows stale data)."""

    return {"dataset_id": dataset_id, **settings}


def _kpi_cards(recommendations):

    summary = InventoryMetrics.summarize(recommendations)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        metric_card("Products to Reorder", summary["products_to_reorder"])

    with c2:

        metric_card("Critical Stock-outs", summary["critical_stockouts"])

    with c3:

        metric_card("Overstocked Products", summary["overstocked_products"])

    with c4:

        metric_card(

            "Inventory Value",

            (

                f"{summary['inventory_value']:,.0f}"

                if summary["inventory_value"] is not None

                else "n/a"

            )

        )

    with c5:

        metric_card(

            "Avg. Days Remaining",

            (

                f"{summary['avg_days_remaining']:.1f}"

                if summary["avg_days_remaining"] is not None

                else "n/a"

            )

        )


def _risk_breakdown(recommendations):

    breakdown = InventoryMetrics.risk_breakdown(recommendations)

    st.caption(
        "🔴 Critical: {Critical}   🟠 High: {High}   "
        "🟡 Medium: {Medium}   🟢 Low: {Low}".format(**breakdown)
    )


def inventory_dashboard():

    page_header(

        "🏭 Inventory Optimization",

        "Turn demand forecasts into reorder recommendations."

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

    latest_forecast = ForecastService.get_latest_batch_forecast(
        dataset_id
    )

    if latest_forecast is None:

        st.warning(

            "No batch forecast found for this dataset. Go to "

            "📈 Forecast → **Batch Forecast — All Products** and run "

            "it first, then come back here."

        )

        page_footer()

        return

    st.caption(

        f"ℹ Using batch forecast from "

        f"{latest_forecast.created_at:%Y-%m-%d %H:%M} "

        f"({latest_forecast.granularity}, "

        f"{latest_forecast.horizon}-period horizon)."

    )

    settings = _settings_controls()

    run = st.button("🚀 Run Inventory Optimization", type="primary")

    if run:

        try:

            with st.spinner("Computing reorder recommendations..."):

                result = InventoryService.generate_recommendations(

                    dataset_id,

                    lead_time_days=settings["lead_time_days"],

                    review_period_days=settings["review_period_days"],

                    service_level=settings["service_level"],

                    overstock_factor=settings["overstock_factor"]

                )

            st.session_state.last_inventory_run = {

                "params": _run_params(dataset_id, settings),

                "result": result

            }

        except ValueError as error:

            st.warning(str(error))

            st.session_state.pop("last_inventory_run", None)

    stored = st.session_state.get("last_inventory_run")

    if (

            not stored

            or stored["params"] != _run_params(dataset_id, settings)

    ):

        st.info(
            "Choose your settings and click **Run Inventory "
            "Optimization** to generate recommendations."
        )

        page_footer()

        return

    result = stored["result"]

    recommendations = result["recommendations"]

    st.divider()

    st.subheader("Summary")

    _kpi_cards(recommendations)

    _risk_breakdown(recommendations)

    for note in result["notes"]:

        st.caption(f"ℹ {note}")

    st.divider()

    render_recommendations(dataset_id, recommendations)

    page_footer()
