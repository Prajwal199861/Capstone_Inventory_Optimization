"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : report_charts.py

Description :
Milestone 4 - Phase 3: matplotlib figure builders for the Reports
page. Pure functions - data in, a Figure out, no Streamlit and no
report-DTO knowledge - so the exact same Figure object can be shown
live (st.pyplot) and embedded in the PDF export without maintaining
two separate chart implementations (one interactive, one static).

matplotlib (not Plotly) is used specifically for this page: it needs
no browser-engine dependency (unlike Plotly's kaleido) to rasterize
charts for the PDF, and a printable, meeting-ready report has no need
for hover tooltips. The rest of the app's interactive pages keep
using Plotly - this is a deliberate, page-scoped choice, not a
project-wide charting change.
=============================================================================
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


PALETTE = [

    "#1565C0",

    "#26A69A",

    "#F9A825",

    "#E53935",

    "#8E24AA",

    "#43A047"

]

RISK_COLORS = {

    "Critical": "#E53935",

    "High": "#F9A825",

    "Medium": "#FDD835",

    "Low": "#43A047"

}


def _empty_axes(
        figure: Figure,
        message: str = "No data available"
):

    axes = figure.subplots()

    axes.text(

        0.5,

        0.5,

        message,

        ha="center",

        va="center",

        color="#9E9E9E"

    )

    axes.axis("off")

    return axes


def risk_pie_chart(
        risk_counts: dict,
        title: str = "Inventory Risk Distribution"
) -> Figure:
    """Pie chart of {"Critical", "High", "Medium", "Low"} -> count."""

    figure = Figure(figsize=(5, 4))

    total = sum(risk_counts.values()) if risk_counts else 0

    if not total:

        _empty_axes(figure)

        figure.suptitle(title)

        return figure

    labels = [

        level

        for level in ["Critical", "High", "Medium", "Low"]

        if risk_counts.get(level, 0) > 0

    ]

    values = [risk_counts[level] for level in labels]

    colors = [RISK_COLORS[level] for level in labels]

    axes = figure.subplots()

    axes.pie(

        values,

        labels=labels,

        autopct="%1.0f%%",

        colors=colors,

        startangle=90

    )

    axes.set_title(title)

    figure.tight_layout()

    return figure


def category_bar_chart(
        table,
        category_column: str,
        value_column: str,
        title: str = "",
        ylabel: str = ""
) -> Figure:
    """Vertical bar chart of one numeric column grouped by category -
    used for "Forecast Demand by Category" / "Inventory Value by
    Category" (Executive Dashboard and Product Performance Report)."""

    figure = Figure(figsize=(6, 4))

    if table is None or table.empty:

        _empty_axes(figure)

        figure.suptitle(title)

        return figure

    axes = figure.subplots()

    axes.bar(

        table[category_column].astype(str),

        table[value_column],

        color=PALETTE[0]

    )

    axes.set_title(title)

    if ylabel:

        axes.set_ylabel(ylabel)

    for label in axes.get_xticklabels():

        label.set_rotation(45)

        label.set_ha("right")

    figure.tight_layout()

    return figure


def top_products_bar_chart(
        table,
        name_column: str,
        value_column: str,
        title: str = "",
        xlabel: str = ""
) -> Figure:
    """Horizontal bar chart, highest value at the top - used for
    "Top 10/20 Products by Forecast Demand" and similar rankings."""

    figure = Figure(figsize=(6, 5))

    if table is None or table.empty:

        _empty_axes(figure)

        figure.suptitle(title)

        return figure

    ordered = table.iloc[::-1]

    axes = figure.subplots()

    axes.barh(

        ordered[name_column].astype(str),

        ordered[value_column],

        color=PALETTE[1]

    )

    axes.set_title(title)

    if xlabel:

        axes.set_xlabel(xlabel)

    figure.tight_layout()

    return figure


def inventory_position_chart(
        totals: dict,
        title: str = "Inventory Position"
) -> Figure:
    """Bar chart of aggregate Current/Safety/Reorder(/Recommended)
    totals - used by the Inventory Report."""

    figure = Figure(figsize=(6, 4))

    if not totals:

        _empty_axes(figure)

        figure.suptitle(title)

        return figure

    labels = list(totals.keys())

    values = list(totals.values())

    axes = figure.subplots()

    axes.bar(labels, values, color=PALETTE[:len(labels)])

    axes.set_title(title)

    axes.set_ylabel("Units")

    for label in axes.get_xticklabels():

        label.set_rotation(15)

        label.set_ha("right")

    figure.tight_layout()

    return figure


def forecast_trend_chart(
        trend,
        history=None,
        measure: str = "Quantity",
        title: str = "Forecast Trend"
) -> Figure:
    """
    Line chart: historical demand (if available) + forecast, with a
    shaded confidence band when the forecast carries Lower/Upper
    bounds. `trend` is [Period, Forecast, Lower, Upper];
    `history` is a DataFrame indexed by Period with one column named
    after `measure` (DemandService's series shape), or None.
    """

    figure = Figure(figsize=(7, 4))

    has_history = history is not None and not history.empty

    has_trend = trend is not None and not trend.empty

    if not has_history and not has_trend:

        _empty_axes(figure)

        figure.suptitle(title)

        return figure

    axes = figure.subplots()

    if has_history:

        axes.plot(

            history.index,

            history[measure],

            label="Historical",

            color=PALETTE[0]

        )

    if has_trend:

        if trend["Lower"].notna().all() and trend["Upper"].notna().all():

            axes.fill_between(

                trend["Period"],

                trend["Lower"],

                trend["Upper"],

                color=PALETTE[1],

                alpha=0.2,

                label="Confidence Band"

            )

        axes.plot(

            trend["Period"],

            trend["Forecast"],

            label="Forecast",

            color=PALETTE[1],

            linestyle="--"

        )

    axes.set_title(title)

    axes.set_ylabel(measure)

    axes.legend()

    for label in axes.get_xticklabels():

        label.set_rotation(30)

        label.set_ha("right")

    figure.tight_layout()

    return figure
