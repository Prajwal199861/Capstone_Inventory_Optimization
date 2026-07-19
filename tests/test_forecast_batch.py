"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_forecast_batch.py

Description :
Unit tests for the Phase 2C batch forecasting core: per-product
forecasts, skip-with-reason handling, per-product forecast points
and progress reporting. Pure logic tests - no database access.

Run with either:
    python tests/test_forecast_batch.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from services.forecast_service import ForecastService


def product_series(n, level):

    index = pd.date_range("2025-01-01", periods=n, freq="D")

    return pd.Series(np.full(n, float(level)), index=index)


def sample_series_map():

    return {

        "P1": product_series(90, 10),

        "P2": product_series(90, 50),

        "SHORT": product_series(20, 5)   # too little history

    }


NAMES = {

    "P1": "Chair",

    "P2": "Table",

    "SHORT": "Lamp"

}


def test_batch_forecasts_products_with_history():

    rows, points = ForecastService._batch_from_series_map(

        sample_series_map(), NAMES, horizon=30, granularity="Daily"

    )

    by_id = {row["Product ID"]: row for row in rows}

    assert by_id["P1"]["Status"] == "Forecast"

    assert by_id["P2"]["Status"] == "Forecast"

    # Flat series: total forecast = horizon x level
    assert abs(by_id["P1"]["Total Forecast"] - 300.0) < 5

    assert abs(by_id["P2"]["Total Forecast"] - 1500.0) < 25

    assert by_id["P1"]["Product Name"] == "Chair"


def test_batch_skips_short_history_with_reason():

    rows, points = ForecastService._batch_from_series_map(

        sample_series_map(), NAMES, horizon=30, granularity="Daily"

    )

    short = next(
        row for row in rows if row["Product ID"] == "SHORT"
    )

    assert short["Status"].startswith("Skipped:")

    assert "Not enough history" in short["Status"]

    assert short["Total Forecast"] is None

    # A skipped product contributes no points
    assert not any(
        point.product_id == "SHORT" for point in points
    )


def test_batch_points_carry_product_id_and_horizon():

    rows, points = ForecastService._batch_from_series_map(

        sample_series_map(), NAMES, horizon=30, granularity="Daily"

    )

    # Two forecastable products x 30 periods
    assert len(points) == 60

    product_ids = {point.product_id for point in points}

    assert product_ids == {"P1", "P2"}

    for point in points:

        assert point.lower is not None

        assert point.upper is not None

        assert point.lower <= point.value <= point.upper


def test_batch_never_fails_whole_run():

    series_map = {

        "OK": product_series(90, 10),

        "EMPTY": product_series(1, 0)

    }

    rows, points = ForecastService._batch_from_series_map(

        series_map, {}, horizon=30, granularity="Daily"

    )

    statuses = {row["Product ID"]: row["Status"] for row in rows}

    assert statuses["OK"] == "Forecast"

    assert statuses["EMPTY"].startswith("Skipped:")


def test_batch_progress_callback_reports_every_product():

    calls = []

    ForecastService._batch_from_series_map(

        sample_series_map(),

        NAMES,

        horizon=30,

        granularity="Daily",

        progress_callback=lambda done, total, pid: calls.append(
            (done, total)
        )

    )

    assert calls == [(1, 3), (2, 3), (3, 3)]


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
