"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : forecast.py

Description :
Milestone 3 - Phase 2A: Forecast page (demand history view).
Lets the user pick a READY dataset, granularity, measure and optional
filters, then shows the historical demand series that the Phase 2B
Forecast Engine will consume. No business logic lives here.
=============================================================================
"""

import plotly.graph_objects as go
import streamlit as st

from components.header import page_header
from components.footer import page_footer

from services.demand_service import DemandService


ALL_OPTION = "All"


def _demand_controls(dataset_id: int):
    """Render series controls; returns build_demand_series kwargs.

    Reused by Phase 2B when forecasting is added on top of the
    history view."""

    c1, c2 = st.columns(2)

    with c1:

        granularity = st.selectbox(

            "Granularity",

            list(DemandService.GRANULARITY_FREQUENCIES.keys()),

            index=2

        )

    with c2:

        measure = st.selectbox(

            "Measure",

            DemandService.MEASURES

        )

    options = DemandService.get_filter_options(dataset_id)

    product_id = None

    store_id = None

    category = None

    f1, f2, f3 = st.columns(3)

    if options["products"]:

        with f1:

            labels = {ALL_OPTION: ALL_OPTION}

            for value, name in options["products"]:

                labels[f"{name} ({value})"] = value

            selected = st.selectbox(

                "Product",

                list(labels.keys())

            )

            if selected != ALL_OPTION:

                product_id = labels[selected]

    if options["stores"]:

        with f2:

            selected = st.selectbox(

                "Store",

                [ALL_OPTION] + options["stores"]

            )

            if selected != ALL_OPTION:

                store_id = selected

    if options["categories"]:

        with f3:

            selected = st.selectbox(

                "Category",

                [ALL_OPTION] + options["categories"]

            )

            if selected != ALL_OPTION:

                category = selected

    return {

        "granularity": granularity,

        "measure": measure,

        "product_id": product_id,

        "store_id": store_id,

        "category": category

    }


def _history_chart(series, measure: str):

    figure = go.Figure()

    figure.add_trace(

        go.Scatter(

            x=series.index,

            y=series[measure],

            mode="lines",

            name=f"Historical {measure}",

            line=dict(color="#1565C0")

        )

    )

    figure.update_layout(

        margin=dict(l=10, r=10, t=30, b=10),

        xaxis_title="Period",

        yaxis_title=measure,

        height=420

    )

    st.plotly_chart(

        figure,

        use_container_width=True

    )


def forecast():

    page_header(

        "📈 Forecast",

        "Demand history and forecasting on standardized datasets."

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

    selected = st.selectbox(

        "Dataset",

        list(dataset_labels.keys())

    )

    dataset_id = dataset_labels[selected]

    try:

        controls = _demand_controls(dataset_id)

        result = DemandService.build_demand_series(

            dataset_id,

            **controls

        )

    except ValueError as error:

        st.warning(str(error))

        page_footer()

        return

    series = result["series"]

    measure = result["measure"]

    if series.empty:

        st.warning(

            "No demand data for the selected filters."

        )

        page_footer()

        return

    st.subheader("Demand History")

    m1, m2, m3 = st.columns(3)

    m1.metric(

        "Periods",

        f"{len(series):,}"

    )

    m2.metric(

        f"Total {measure}",

        f"{series[measure].sum():,.0f}"

    )

    m3.metric(

        "Date Range",

        f"{series.index.min():%Y-%m-%d} → "

        f"{series.index.max():%Y-%m-%d}"

    )

    _history_chart(series, measure)

    for note in result["notes"]:

        st.caption(f"ℹ {note}")

    st.info(

        "Forecast generation arrives in the next phase. This view "

        "shows the exact series the forecast engine will use."

    )

    page_footer()
