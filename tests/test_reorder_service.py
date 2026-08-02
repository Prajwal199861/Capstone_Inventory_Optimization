"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_reorder_service.py

Description :
Unit tests for the Phase 3 ReorderService: wiring the
InventoryCalculator formulas together into one product's stock
position. Pure logic tests - no database access.

Run with either:
    python tests/test_reorder_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.reorder_service import ReorderService


def test_compute_position_healthy_stock_orders_nothing():

    position = ReorderService.compute_position(

        current_stock=500,

        forecast_total=300,

        forecast_periods=30,

        granularity="Daily",

        lead_time_days=7,

        review_period_days=7

    )

    assert position["daily_avg_demand"] == 10.0

    assert position["recommended_quantity"] == 0.0

    assert position["days_remaining"] == 50.0


def test_compute_position_low_stock_recommends_reorder():

    position = ReorderService.compute_position(

        current_stock=20,

        forecast_total=300,

        forecast_periods=30,

        granularity="Daily",

        lead_time_days=7,

        review_period_days=7

    )

    assert position["recommended_quantity"] > 0

    assert position["reorder_point"] > 20


def test_compute_position_respects_safety_stock_override():

    position = ReorderService.compute_position(

        current_stock=200,

        forecast_total=300,

        forecast_periods=30,

        granularity="Daily",

        lead_time_days=7,

        safety_stock_override=999

    )

    assert position["safety_stock"] == 999.0

    assert position["reorder_point"] >= 999.0


def test_compute_position_no_forecast_demand_still_computable():

    # Product with zero forecast demand should not crash, and should
    # not falsely recommend a reorder purely from a floor buffer.
    position = ReorderService.compute_position(

        current_stock=10,

        forecast_total=0,

        forecast_periods=30,

        granularity="Daily",

        lead_time_days=7

    )

    assert position["daily_avg_demand"] == 0.0

    assert position["days_remaining"] is None


def test_service_level_z_defaults_when_unknown():

    assert ReorderService.service_level_z(0.5) == (

        ReorderService.service_level_z(0.95)

    )


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
