"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_inventory_calculator.py

Description :
Unit tests for the Phase 3 inventory formulas (InventoryCalculator).
Pure math tests - no database, no pandas.

Run with either:
    python tests/test_inventory_calculator.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.inventory_calculator import InventoryCalculator


def test_daily_average_demand():

    assert InventoryCalculator.daily_average_demand(300, 30) == 10.0

    # Zero/negative horizon must not divide-by-zero.
    assert InventoryCalculator.daily_average_demand(300, 0) == 0.0


def test_demand_during_lead_time():

    assert InventoryCalculator.demand_during_lead_time(10, 7) == 70.0


def test_safety_stock_uses_statistical_formula_when_std_known():

    safety = InventoryCalculator.safety_stock(

        daily_average_demand=10,

        lead_time_days=9,

        daily_demand_std=2,

        service_level_z=1.65,

        minimum_days=0

    )

    # 1.65 * 2 * sqrt(9) = 9.9
    assert abs(safety - 9.9) < 0.01


def test_safety_stock_falls_back_to_minimum_days_floor():

    # No std known -> plain days-of-cover buffer.
    safety = InventoryCalculator.safety_stock(

        daily_average_demand=10,

        lead_time_days=7,

        daily_demand_std=None,

        minimum_days=3

    )

    assert safety == 30.0


def test_safety_stock_keeps_the_larger_of_statistical_and_floor():

    safety = InventoryCalculator.safety_stock(

        daily_average_demand=10,

        lead_time_days=1,

        daily_demand_std=0.1,

        service_level_z=1.65,

        minimum_days=5

    )

    # Statistical (~0.165) is tiny; the 5-day floor (50) wins.
    assert safety == 50.0


def test_reorder_point():

    assert InventoryCalculator.reorder_point(70, 20) == 90


def test_target_stock_level():

    # (lead 7 + review 7) days * 10/day + 20 safety stock = 160
    target = InventoryCalculator.target_stock_level(
        daily_average_demand=10,
        lead_time_days=7,
        review_period_days=7,
        safety_stock=20
    )

    assert target == 160.0


def test_available_inventory():

    assert InventoryCalculator.available_inventory(100, 20, 10) == 110


def test_days_of_inventory_remaining():

    assert InventoryCalculator.days_of_inventory_remaining(100, 10) == 10.0

    # No demand -> unknown, not "infinite" or "zero".
    assert InventoryCalculator.days_of_inventory_remaining(100, 0) is None


def test_recommended_reorder_quantity_above_reorder_point_orders_nothing():

    quantity = InventoryCalculator.recommended_reorder_quantity(

        available_inventory=200,

        reorder_point=90,

        target_stock_level=160

    )

    assert quantity == 0.0


def test_recommended_reorder_quantity_orders_up_to_target():

    quantity = InventoryCalculator.recommended_reorder_quantity(

        available_inventory=50,

        reorder_point=90,

        target_stock_level=160

    )

    assert quantity == 110.0


def test_recommended_reorder_quantity_respects_minimum_and_multiple():

    quantity = InventoryCalculator.recommended_reorder_quantity(

        available_inventory=50,

        reorder_point=90,

        target_stock_level=160,

        minimum_order_quantity=120,

        order_multiple=25

    )

    # max(110, 120) = 120 -> rounded up to nearest 25 = 125
    assert quantity == 125.0


def test_recommended_reorder_quantity_capped_at_maximum_stock():

    quantity = InventoryCalculator.recommended_reorder_quantity(

        available_inventory=50,

        reorder_point=90,

        target_stock_level=500,

        maximum_stock=100

    )

    # Headroom to max stock is only 50 units.
    assert quantity == 50.0


def test_inventory_value_none_without_unit_cost():

    assert InventoryCalculator.inventory_value(100, None) is None

    assert InventoryCalculator.inventory_value(100, 2.5) == 250.0


def test_excess_units():

    # 100 units on hand, 20 forecast, 2x threshold -> excess above 40
    assert InventoryCalculator.excess_units(100, 20, 2.0) == 60.0

    assert InventoryCalculator.excess_units(30, 20, 2.0) == 0.0

    # No forecast demand -> no evidence of excess.
    assert InventoryCalculator.excess_units(1000, 0, 2.0) == 0.0


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
