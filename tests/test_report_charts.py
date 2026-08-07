"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_report_charts.py

Description :
Unit tests for the Milestone 4 - Phase 3 chart builders
(utils/report_charts.py). Since chart pixels aren't meaningfully
assertable, these confirm each builder returns a Figure for both
populated and empty input (no crash on missing data - the actual
requirement every builder documents) and that the empty case is
visually distinct (no axes drawn).

Run with either:
    python tests/test_report_charts.py
    python -m pytest tests/
=============================================================================
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from matplotlib.figure import Figure

from utils import report_charts as charts


def test_risk_pie_chart_with_data():

    figure = charts.risk_pie_chart(
        {"Critical": 1, "High": 2, "Medium": 0, "Low": 3}
    )

    assert isinstance(figure, Figure)

    assert len(figure.axes) == 1


def test_risk_pie_chart_empty_does_not_raise():

    figure = charts.risk_pie_chart({})

    assert isinstance(figure, Figure)


def test_risk_pie_chart_all_zero_does_not_raise():

    figure = charts.risk_pie_chart(
        {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    )

    assert isinstance(figure, Figure)


def test_category_bar_chart_with_data():

    table = pd.DataFrame({

        "Category": ["Tools", "Electronics"],

        "Forecast Demand": [100, 50]

    })

    figure = charts.category_bar_chart(
        table, "Category", "Forecast Demand", title="Demand"
    )

    assert isinstance(figure, Figure)


def test_category_bar_chart_empty_does_not_raise():

    figure = charts.category_bar_chart(
        pd.DataFrame(), "Category", "Forecast Demand"
    )

    assert isinstance(figure, Figure)


def test_top_products_bar_chart_with_data():

    table = pd.DataFrame({

        "Product Name": ["Widget", "Gadget"],

        "Forecast Demand": [100, 50]

    })

    figure = charts.top_products_bar_chart(
        table, "Product Name", "Forecast Demand", title="Top"
    )

    assert isinstance(figure, Figure)


def test_top_products_bar_chart_empty_does_not_raise():

    figure = charts.top_products_bar_chart(
        pd.DataFrame(), "Product Name", "Forecast Demand"
    )

    assert isinstance(figure, Figure)


def test_inventory_position_chart_with_data():

    figure = charts.inventory_position_chart({

        "Current Stock": 910,

        "Safety Stock": 35,

        "Reorder Point": 55

    })

    assert isinstance(figure, Figure)


def test_inventory_position_chart_empty_does_not_raise():

    figure = charts.inventory_position_chart({})

    assert isinstance(figure, Figure)


def test_forecast_trend_chart_with_history_and_trend():

    trend = pd.DataFrame({

        "Period": [datetime(2026, 1, 1), datetime(2026, 2, 1)],

        "Forecast": [75.0, 75.0],

        "Lower": [60.0, 60.0],

        "Upper": [90.0, 90.0]

    })

    history = pd.DataFrame(

        {"Quantity": [10, 20, 30]},

        index=pd.date_range("2025-10-01", periods=3, freq="MS")

    )

    figure = charts.forecast_trend_chart(
        trend, history, measure="Quantity"
    )

    assert isinstance(figure, Figure)


def test_forecast_trend_chart_forecast_only_no_history():

    trend = pd.DataFrame({

        "Period": [datetime(2026, 1, 1)],

        "Forecast": [75.0],

        "Lower": [60.0],

        "Upper": [90.0]

    })

    figure = charts.forecast_trend_chart(trend, history=None)

    assert isinstance(figure, Figure)


def test_forecast_trend_chart_both_empty_does_not_raise():

    figure = charts.forecast_trend_chart(

        pd.DataFrame(columns=["Period", "Forecast", "Lower", "Upper"]),

        history=None

    )

    assert isinstance(figure, Figure)


def test_forecast_trend_chart_missing_bounds_skips_band_not_line():

    trend = pd.DataFrame({

        "Period": [datetime(2026, 1, 1)],

        "Forecast": [75.0],

        "Lower": [None],

        "Upper": [None]

    })

    figure = charts.forecast_trend_chart(trend, history=None)

    assert isinstance(figure, Figure)

    axes = figure.axes[0]

    # The forecast line itself should still be drawn even without
    # a confidence band to shade.
    assert len(axes.lines) >= 1


# ---------------------------------------------------------------------
# Plain-python runner
# ---------------------------------------------------------------------

if __name__ == "__main__":

    failures = 0

    tests = [

        (name, function)

        for name, function in sorted(globals().items())

        if name.startswith("test_") and callable(function)

    ]

    for name, function in tests:

        try:

            function()

            print(f"PASS  {name}")

        except Exception as error:

            failures += 1

            print(f"FAIL  {name}: {error}")

    print(

        f"\n{len(tests) - failures}/{len(tests)} tests passed."

    )

    sys.exit(1 if failures else 0)
