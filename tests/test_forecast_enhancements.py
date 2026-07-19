"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_forecast_enhancements.py

Description :
Unit tests for the Phase 2D enhancements: holiday-effect insight,
currency normalization and horizon-widening confidence bands.
Pure logic tests - no database access.

Run with either:
    python tests/test_forecast_enhancements.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from services.demand_service import DemandService
from services.forecast_service import ForecastService


# ---------------------------------------------------------------------
# Holiday effect
# ---------------------------------------------------------------------

def daily_series_with_holidays(holiday_level, base_level=100.0):

    index = pd.date_range("2025-01-01", periods=30, freq="D")

    values = np.full(30, base_level)

    holidays = [index[9], index[19]]

    for day in holidays:

        values[index.get_loc(day)] = holiday_level

    return pd.Series(values, index=index), holidays


def test_holiday_note_triggers_above_threshold():

    series, holidays = daily_series_with_holidays(180.0)

    note = DemandService.holiday_effect_note(series, holidays)

    assert note is not None

    assert "higher" in note

    assert "80%" in note


def test_holiday_note_reports_lower_demand():

    series, holidays = daily_series_with_holidays(40.0)

    note = DemandService.holiday_effect_note(series, holidays)

    assert note is not None

    assert "lower" in note


def test_holiday_note_silent_below_threshold():

    series, holidays = daily_series_with_holidays(110.0)

    assert DemandService.holiday_effect_note(series, holidays) is None


def test_holiday_note_silent_without_holidays():

    series, _ = daily_series_with_holidays(180.0)

    assert DemandService.holiday_effect_note(series, []) is None


def test_truthy_flag_semantics():

    assert DemandService._is_truthy_flag("Yes")

    assert DemandService._is_truthy_flag("Diwali")

    assert DemandService._is_truthy_flag(1)

    assert not DemandService._is_truthy_flag("0")

    assert not DemandService._is_truthy_flag("No")

    assert not DemandService._is_truthy_flag("")

    assert not DemandService._is_truthy_flag(None)

    assert not DemandService._is_truthy_flag(float("nan"))


# ---------------------------------------------------------------------
# Currency normalization
# ---------------------------------------------------------------------

def currency_sales():

    return pd.DataFrame({

        "Transaction Date": pd.to_datetime([
            "2025-01-10", "2025-01-10", "2025-01-20"
        ]),

        "Product ID": ["P1", "P2", "P1"],

        "Quantity": [1, 2, 3],

        "Revenue": [200.0, 300.0, 400.0],

        "Currency": ["EUR", "USD", "INR"]

    })


def currency_rates():

    return pd.DataFrame({

        "Date": pd.to_datetime([
            "2025-01-01", "2025-01-01", "2025-01-01"
        ]),

        "Currency": ["USD", "EUR", "INR"],

        "Rate": [1.0, 2.0, 80.0]

    })


def test_currency_conversion_divides_by_rate():

    sales, notes = DemandService._normalize_currency(
        currency_sales(), currency_rates()
    )

    # EUR 200/2=100, USD 300/1=300, INR 400/80=5
    assert sales["Revenue"].tolist() == [100.0, 300.0, 5.0]

    assert any("normalized to USD" in note for note in notes)


def test_currency_uses_most_recent_prior_rate():

    rates = pd.concat([

        currency_rates(),

        pd.DataFrame({

            "Date": pd.to_datetime(["2025-01-15"]),

            "Currency": ["INR"],

            "Rate": [100.0]

        })

    ])

    sales, _ = DemandService._normalize_currency(
        currency_sales(), rates
    )

    # INR sale on Jan 20 must use the Jan 15 rate (100), not Jan 1
    assert sales["Revenue"].tolist()[-1] == 4.0


def test_currency_skips_silently_without_rates():

    original = currency_sales()

    sales, notes = DemandService._normalize_currency(original, None)

    assert notes == []

    assert sales["Revenue"].tolist() == [200.0, 300.0, 400.0]


def test_currency_skips_silently_without_currency_field():

    sales_frame = currency_sales().drop(columns=["Currency"])

    sales, notes = DemandService._normalize_currency(
        sales_frame, currency_rates()
    )

    assert notes == []


def test_currency_missing_rate_keeps_original_with_note():

    sales_frame = currency_sales()

    sales_frame.loc[2, "Currency"] = "GBP"   # no GBP rate exists

    sales, notes = DemandService._normalize_currency(
        sales_frame, currency_rates()
    )

    assert sales["Revenue"].tolist()[-1] == 400.0

    assert any("no matching exchange rate" in note for note in notes)


# ---------------------------------------------------------------------
# Widening confidence bands
# ---------------------------------------------------------------------

def test_band_width_grows_with_horizon():

    values = np.full(10, 100.0)

    lower, upper = ForecastService._confidence_bounds(
        values, rmse=10.0
    )

    widths = upper - lower

    assert all(np.diff(widths) > 0) or all(

        # Lower is clipped at 0, so check the upper margin instead
        np.diff(upper - values) > 0

    )

    assert abs(
        (upper[3] - values[3]) / (upper[0] - values[0]) - 2.0
    ) < 1e-9   # sqrt(4)/sqrt(1) = 2


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
