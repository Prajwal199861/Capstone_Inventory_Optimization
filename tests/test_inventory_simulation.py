"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_inventory_simulation.py

Description :
Unit tests for InventorySimulationService.simulate_current_stock -
the historical-sales replay that replaces the "assumed = target
level" static fallback (Hotfix Phase 1) so a low-volume product's
estimated stock reflects real usage instead of inflating "Days
Remaining" into the millions.

Run with either:
    python tests/test_inventory_simulation.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from services.inventory_simulation import InventorySimulationService


def test_none_history_returns_none():

    assert InventorySimulationService.simulate_current_stock(
        None,
        opening_stock=200,
        reorder_point=50,
        target_stock_level=200
    ) is None


def test_too_short_history_returns_none():

    # MIN_SIMULATION_HISTORY_PERIODS is 3 - two points is not enough
    # to trust a simulated trajectory.
    short_history = pd.Series([10.0, 15.0])

    assert InventorySimulationService.simulate_current_stock(
        short_history,
        opening_stock=200,
        reorder_point=50,
        target_stock_level=200
    ) is None


def test_depletes_without_crossing_reorder_point():

    history = pd.Series([10.0, 15.0, 25.0])

    result = InventorySimulationService.simulate_current_stock(
        history,
        opening_stock=200,
        reorder_point=50,
        target_stock_level=200
    )

    assert result == 200 - 10 - 15 - 25


def test_replenishes_once_reorder_point_is_crossed():

    # 200 -> 140 -> 80 -> 20 (<= 50, replenish +150) -> 170
    history = pd.Series([60.0, 60.0, 60.0])

    result = InventorySimulationService.simulate_current_stock(
        history,
        opening_stock=200,
        reorder_point=50,
        target_stock_level=200
    )

    assert result == 170


def test_replenishes_multiple_times_across_a_longer_history():

    # 200 -140 -80 -20(+150=170) -110 -50(+150=200) -140
    history = pd.Series([60.0] * 6)

    result = InventorySimulationService.simulate_current_stock(
        history,
        opening_stock=200,
        reorder_point=50,
        target_stock_level=200
    )

    assert result == 140


def test_stock_never_goes_negative_on_a_demand_spike():

    history = pd.Series([100.0, 0.0, 0.0])

    result = InventorySimulationService.simulate_current_stock(
        history,
        opening_stock=10,
        reorder_point=5,
        target_stock_level=10
    )

    # p1: max(10-100,0)=0 <=5 -> +5=5
    # p2: 5-0=5 <=5 -> +5=10
    # p3: 10-0=10 (>5, no replenish)
    assert result == 10


def test_zero_reorder_quantity_never_replenishes():

    # reorder_point == target_stock_level: this is exactly the
    # near-zero-demand edge case that caused the original bug - a
    # product whose safety-stock-driven target already sits at its
    # own reorder trigger. Simulation should drain toward 0 instead of
    # staying pinned at the inflated assumed level forever.
    history = pd.Series([1.0, 1.0, 1.0, 1.0, 10.0])

    result = InventorySimulationService.simulate_current_stock(
        history,
        opening_stock=5,
        reorder_point=5,
        target_stock_level=5
    )

    assert result == 0


def test_realistic_low_volume_product_no_longer_blows_up():

    # The bug scenario: tiny average demand, but safety stock (driven
    # by volatility, not the mean) is a few units - previously this
    # product's assumed stock stayed pinned at ~target level forever,
    # producing "days remaining" in the thousands/millions once
    # divided by a near-zero daily average. After replaying real
    # (mostly zero, occasionally spiky) historical demand, the ending
    # stock should be small, not the inflated target.
    history = pd.Series([0.0, 0.0, 3.0, 0.0, 0.0, 2.0, 0.0, 0.0])

    result = InventorySimulationService.simulate_current_stock(
        history,
        opening_stock=2.6,
        reorder_point=2.6,
        target_stock_level=2.6
    )

    assert result is not None

    assert result < 2.6


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
