"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_stock_risk_service.py

Description :
Unit tests for the Phase 3 business rules (StockRiskService): the
Status/Risk Level/Reason a stock position resolves to. Pure logic
tests - no database access.

Run with either:
    python tests/test_stock_risk_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.stock_risk_service import StockRiskService


def test_out_of_stock_is_critical():

    result = StockRiskService.classify(

        current_stock=0,

        available_inventory=0,

        reorder_point=50,

        safety_stock=20,

        forecast_demand=100,

        excess_units=0,

        days_remaining=None,

        lead_time_days=7

    )

    assert result["risk_level"] == "Critical"

    assert result["status"] == "Reorder Required"


def test_below_safety_stock_is_high_risk():

    result = StockRiskService.classify(

        current_stock=10,

        available_inventory=10,

        reorder_point=50,

        safety_stock=20,

        forecast_demand=100,

        excess_units=0,

        days_remaining=5,

        lead_time_days=7

    )

    assert result["risk_level"] == "High"

    assert result["status"] == "Reorder Required"


def test_will_stock_out_before_lead_time_is_critical():

    result = StockRiskService.classify(

        current_stock=30,

        available_inventory=30,

        reorder_point=50,

        safety_stock=20,

        forecast_demand=100,

        excess_units=0,

        days_remaining=3,

        lead_time_days=7

    )

    assert result["risk_level"] == "Critical"


def test_at_or_below_reorder_point_is_medium():

    result = StockRiskService.classify(

        current_stock=45,

        available_inventory=45,

        reorder_point=50,

        safety_stock=20,

        forecast_demand=100,

        excess_units=0,

        days_remaining=20,

        lead_time_days=7

    )

    assert result["risk_level"] == "Medium"

    assert result["status"] == "Reorder Required"


def test_overstock_warning():

    result = StockRiskService.classify(

        current_stock=500,

        available_inventory=500,

        reorder_point=50,

        safety_stock=20,

        forecast_demand=100,

        excess_units=300,

        days_remaining=100,

        lead_time_days=7

    )

    assert result["status"] == "Overstock Warning"

    assert result["risk_level"] == "Low"


def test_healthy_stock_is_adequate():

    result = StockRiskService.classify(

        current_stock=80,

        available_inventory=80,

        reorder_point=50,

        safety_stock=20,

        forecast_demand=100,

        excess_units=0,

        days_remaining=25,

        lead_time_days=7

    )

    assert result["status"] == "Adequate"

    assert result["risk_level"] == "Low"


def test_every_result_carries_a_reason():

    scenarios = [

        (0, 0, 50, 20, 100, 0, None, 7),

        (10, 10, 50, 20, 100, 0, 5, 7),

        (500, 500, 50, 20, 100, 300, 100, 7),

        (80, 80, 50, 20, 100, 0, 25, 7)

    ]

    for scenario in scenarios:

        result = StockRiskService.classify(*scenario)

        assert result["reason"]

        assert result["risk_level"] in StockRiskService.RISK_LEVELS


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
