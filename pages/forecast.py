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

import json

import plotly.graph_objects as go
import streamlit as st

from components.header import page_header
from components.footer import page_footer

from services.demand_service import DemandService
from services.forecast_service import ForecastService

from utils.forecast_models import MODEL_REGISTRY


ALL_OPTION = "All"

# Horizon presets per granularity: label -> number of periods.
HORIZON_PRESETS = {

    "Daily": {

        "30 days": 30,

        "60 days": 60,

        "90 days": 90

    },

    "Weekly": {

        "4 weeks": 4,

        "8 weeks": 8,

        "12 weeks": 12

    },

    "Monthly": {

        "3 months": 3,

        "6 months": 6,

        "12 months": 12

    }

}


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

    # Scope choices adapt to what the dataset actually contains.
    scopes = ["Overall"]

    if options["products"]:

        scopes.append("By Product")

    if options["stores"]:

        scopes.append("By Store")

    if options["categories"]:

        scopes.append("By Category")

    product_id = None

    store_id = None

    category = None

    s1, s2 = st.columns([1, 2])

    with s1:

        scope = st.selectbox(

            "Forecast Scope",

            scopes

        )

    with s2:

        if scope == "By Product":

            labels = {}

            for value, name in options["products"]:

                labels[f"{name} ({value})"] = value

            selected = st.selectbox(

                "Product",

                list(labels.keys())

            )

            product_id = labels[selected]

        elif scope == "By Store":

            store_id = st.selectbox(

                "Store",

                options["stores"]

            )

        elif scope == "By Category":

            category = st.selectbox(

                "Category",

                options["categories"]

            )

    return {

        "granularity": granularity,

        "measure": measure,

        "scope": scope,

        "product_id": product_id,

        "store_id": store_id,

        "category": category

    }


def _history_chart(series, measure: str, holiday_dates=None):

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

    if holiday_dates:

        holidays = series[series.index.isin(holiday_dates)]

        if not holidays.empty:

            figure.add_trace(

                go.Scatter(

                    x=holidays.index,

                    y=holidays[measure],

                    mode="markers",

                    name="Holiday / Festival",

                    marker=dict(

                        color="#E53935",

                        size=9,

                        symbol="diamond"

                    )

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


def _forecast_chart(history, forecast_frame, measure: str):
    """History + forecast with a shaded ~95% confidence band."""

    figure = go.Figure()

    figure.add_trace(

        go.Scatter(

            x=forecast_frame.index,

            y=forecast_frame["Upper"],

            mode="lines",

            line=dict(width=0),

            showlegend=False,

            hoverinfo="skip"

        )

    )

    figure.add_trace(

        go.Scatter(

            x=forecast_frame.index,

            y=forecast_frame["Lower"],

            mode="lines",

            line=dict(width=0),

            fill="tonexty",

            fillcolor="rgba(38, 166, 154, 0.2)",

            name="95% Confidence (widens with horizon)"

        )

    )

    figure.add_trace(

        go.Scatter(

            x=history.index,

            y=history[measure],

            mode="lines",

            name=f"Historical {measure}",

            line=dict(color="#1565C0")

        )

    )

    figure.add_trace(

        go.Scatter(

            x=forecast_frame.index,

            y=forecast_frame["Forecast"],

            mode="lines",

            name="Forecast",

            line=dict(color="#26A69A", dash="dash")

        )

    )

    figure.update_layout(

        margin=dict(l=10, r=10, t=30, b=10),

        xaxis_title="Period",

        yaxis_title=measure,

        height=440

    )

    st.plotly_chart(

        figure,

        use_container_width=True

    )


def _series_params(dataset_id: int, controls: dict) -> dict:
    """Identity of the currently selected series. Stored results are
    only rendered while they still match, so switching dataset or
    scope never shows a stale forecast."""

    return {

        "dataset_id": dataset_id,

        **controls

    }


def _forecast_section(dataset_id: int, controls: dict):
    """Forecast generation controls, chart and metrics."""

    st.divider()

    st.subheader("Generate Forecast")

    granularity = controls["granularity"]

    presets = HORIZON_PRESETS[granularity]

    c1, c2, c3 = st.columns([2, 2, 1])

    with c1:

        horizon_label = st.selectbox(

            "Forecast Horizon",

            list(presets.keys())

        )

    with c2:

        model = st.selectbox(

            "Model",

            [ForecastService.AUTO_MODEL]

            + list(MODEL_REGISTRY.keys())

        )

    with c3:

        st.write("")

        st.write("")

        generate = st.button(

            "🚀 Generate",

            use_container_width=True

        )

    if generate:

        try:

            with st.spinner("Backtesting models and forecasting..."):

                result = ForecastService.generate_forecast(

                    dataset_id,

                    horizon_periods=presets[horizon_label],

                    granularity=granularity,

                    measure=controls["measure"],

                    model=model,

                    created_by=st.session_state.user_id,

                    product_id=controls["product_id"],

                    store_id=controls["store_id"],

                    category=controls["category"],

                    scope=controls["scope"]

                )

            st.session_state.last_forecast = {

                "params": _series_params(dataset_id, controls),

                "result": result

            }

        except ValueError as error:

            st.warning(str(error))

            st.session_state.pop("last_forecast", None)

    stored = st.session_state.get("last_forecast")

    if (

            not stored

            or stored["params"] != _series_params(dataset_id, controls)

    ):

        return

    result = stored["result"]

    measure = result["history"].columns[0]

    chosen = result["model_name"]

    chosen_metrics = result["metrics"][chosen]

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Model", chosen)

    m2.metric(

        "MAPE",

        f"{chosen_metrics['mape']:.1f}%"

        if chosen_metrics["mape"] is not None

        else "n/a"

    )

    m3.metric(

        "RMSE",

        f"{chosen_metrics['rmse']:,.1f}"

    )

    m4.metric(

        f"Total Forecast {measure}",

        f"{result['forecast']['Forecast'].sum():,.0f}"

    )

    _forecast_chart(

        result["history"],

        result["forecast"],

        measure

    )

    with st.expander("📊 Model Accuracy Comparison"):

        comparison = [

            {

                "Model": model_name,

                "MAPE (%)": (

                    round(score["mape"], 2)

                    if score["mape"] is not None

                    else None

                ),

                "RMSE": round(score["rmse"], 2)

            }

            for model_name, score in result["metrics"].items()

        ]

        st.dataframe(

            comparison,

            use_container_width=True

        )

        backtest = result.get("backtest")

        if backtest is not None:

            st.caption(

                "Backtest holdout window: every candidate model's "

                "prediction against what actually happened — this is "

                "why Auto chose its model."

            )

            figure = go.Figure()

            figure.add_trace(

                go.Scatter(

                    x=backtest["index"],

                    y=backtest["actual"],

                    mode="lines+markers",

                    name="Actual",

                    line=dict(color="#1565C0", width=3)

                )

            )

            for model_name, predicted in (
                    backtest["predictions"].items()
            ):

                figure.add_trace(

                    go.Scatter(

                        x=backtest["index"],

                        y=predicted,

                        mode="lines",

                        name=model_name,

                        line=dict(dash="dot")

                    )

                )

            figure.update_layout(

                margin=dict(l=10, r=10, t=30, b=10),

                height=320

            )

            st.plotly_chart(

                figure,

                use_container_width=True

            )

    for note in result["notes"]:

        st.caption(f"ℹ {note}")


def _run_scope(run) -> str:
    """Human-readable scope of a saved run, from its filters JSON."""

    try:

        filters = json.loads(run.filters or "{}")

    except ValueError:

        filters = {}

    if filters.get("scope") == ForecastService.BATCH_SCOPE:

        return "Batch (all products)"

    if filters.get("product_id"):

        return f"Product {filters['product_id']}"

    if filters.get("store_id"):

        return f"Store {filters['store_id']}"

    if filters.get("category"):

        return f"Category {filters['category']}"

    return "Overall"


def _past_forecasts(dataset_id: int):

    runs = ForecastService.list_forecasts(dataset_id)

    if not runs:

        return

    st.divider()

    with st.expander(

            f"🕓 Past Forecasts ({len(runs)})"

    ):

        st.dataframe(

            [

                {

                    "Created": run.created_at.strftime(
                        "%Y-%m-%d %H:%M"
                    ),

                    "Scope": _run_scope(run),

                    "Measure": run.measure,

                    "Granularity": run.granularity,

                    "Horizon": run.horizon,

                    "Model": run.model_name,

                    "MAPE (%)": (

                        round(run.mape, 2)

                        if run.mape is not None

                        else None

                    ),

                    "RMSE": (

                        round(run.rmse, 2)

                        if run.rmse is not None

                        else None

                    )

                }

                for run in runs

            ],

            use_container_width=True

        )


def _batch_section(dataset_id: int, controls: dict):
    """Forecast-all-products batch run with CSV export (Phase 3
    inventory optimization consumes the persisted output)."""

    st.divider()

    st.subheader("Batch Forecast — All Products")

    st.caption(

        "Forecasts every product with sufficient history using Auto "

        "model selection. The saved run feeds inventory optimization."

    )

    b1, b2 = st.columns([1, 3])

    with b1:

        run_batch = st.button(

            "📦 Forecast All Products",

            use_container_width=True

        )

    if run_batch:

        presets = HORIZON_PRESETS[controls["granularity"]]

        horizon = list(presets.values())[0]

        with st.status(

                "Running batch forecast...",

                expanded=False

        ) as status:

            def report(done, total, product_id):

                if done % 10 == 0 or done == total:

                    status.update(

                        label=f"Forecasting product {done}/{total}"

                    )

            try:

                batch = ForecastService.generate_batch(

                    dataset_id,

                    horizon_periods=horizon,

                    granularity=controls["granularity"],

                    measure="Quantity",

                    created_by=st.session_state.user_id,

                    progress_callback=report

                )

                status.update(

                    label="Batch forecast complete",

                    state="complete"

                )

                st.session_state.last_batch = {

                    "dataset_id": dataset_id,

                    "batch": batch

                }

            except ValueError as error:

                status.update(

                    label="Batch forecast failed",

                    state="error"

                )

                st.warning(str(error))

                st.session_state.pop("last_batch", None)

    stored = st.session_state.get("last_batch")

    if not stored or stored["dataset_id"] != dataset_id:

        return

    batch = stored["batch"]

    c1, c2, c3 = st.columns(3)

    c1.metric("Products Forecast", batch["forecasted"])

    c2.metric("Skipped", batch["skipped"])

    c3.metric(

        "Total Forecast Demand",

        f"{batch['summary']['Total Forecast'].sum():,.0f}"

    )

    st.dataframe(

        batch["summary"],

        use_container_width=True

    )

    st.download_button(

        "⬇ Download Summary (CSV)",

        batch["summary"].to_csv(index=False).encode("utf-8"),

        file_name=f"batch_forecast_dataset_{dataset_id}.csv",

        mime="text/csv"

    )

    if batch.get("export_path"):

        st.caption(f"💾 Summary saved to {batch['export_path']}")

    for note in batch["notes"]:

        st.caption(f"ℹ {note}")


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

            granularity=controls["granularity"],

            measure=controls["measure"],

            product_id=controls["product_id"],

            store_id=controls["store_id"],

            category=controls["category"]

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

    holiday_dates = DemandService.get_holiday_periods(dataset_id)

    _history_chart(

        series,

        measure,

        holiday_dates if controls["granularity"] == "Daily" else None

    )

    for note in result["notes"]:

        st.caption(f"ℹ {note}")

    if holiday_dates and controls["granularity"] == "Daily":

        effect = DemandService.holiday_effect_note(

            series[measure],

            holiday_dates

        )

        if effect:

            st.caption(f"🎉 {effect}")

    _forecast_section(dataset_id, controls)

    _batch_section(dataset_id, controls)

    _past_forecasts(dataset_id)

    page_footer()
