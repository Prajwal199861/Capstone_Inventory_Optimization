"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_inventory_service.py

Description :
Unit tests for InventoryService's pure helper steps (demand/price/name
maps built from standardized frames and a saved forecast, plus the
missing-value coercion helpers). The end-to-end
generate_recommendations() path needs the database and is exercised
manually via the Inventory page; these tests cover the joins/formula
wiring without a database.

Run with either:
    python tests/test_inventory_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from services.inventory_service import InventoryService


class _Point:

    def __init__(self, product_id, value, lower=None, upper=None):

        self.product_id = product_id

        self.value = value

        self.lower = lower

        self.upper = upper


class _Forecast:

    def __init__(self, granularity, points):

        self.granularity = granularity

        self.points = points


def test_demand_map_sums_per_product_and_counts_periods():

    forecast = _Forecast("Daily", [

        _Point("P1", 10, 5, 15),

        _Point("P1", 12, 6, 18),

        _Point("P2", 20, 10, 30)

    ])

    demand_map = InventoryService._demand_map(forecast)

    assert demand_map["P1"]["total"] == 22

    assert demand_map["P1"]["periods"] == 2

    assert demand_map["P2"]["total"] == 20

    assert demand_map["P2"]["periods"] == 1


def test_demand_map_estimates_std_from_confidence_band():

    # Band width 10 over 1 day => std = 10 / (2*1.96) / 1 ~= 2.551
    forecast = _Forecast("Daily", [_Point("P1", 10, 5, 15)])

    demand_map = InventoryService._demand_map(forecast)

    assert abs(demand_map["P1"]["daily_std"] - 2.551) < 0.01


def test_demand_map_ignores_overall_scope_points():

    # Non-batch points (product_id None) must never leak in.
    forecast = _Forecast("Daily", [_Point(None, 999)])

    demand_map = InventoryService._demand_map(forecast)

    assert demand_map == {}


def test_price_map_prefers_cost_price_over_selling_price():

    products = pd.DataFrame({

        "Product ID": ["P1", "P2"],

        "Cost Price": [5.0, None],

        "Selling Price": [10.0, 20.0]

    })

    price_map = InventoryService._price_map(products)

    assert price_map["P1"] == 5.0

    assert price_map["P2"] is None


def test_price_map_empty_without_products():

    assert InventoryService._price_map(None) == {}


def test_name_map_maps_ids_to_names():

    products = pd.DataFrame({

        "Product ID": ["P1"],

        "Product Name": ["Chair"]

    })

    assert InventoryService._name_map(products) == {"P1": "Chair"}


def test_numeric_or_falls_back_on_missing_values():

    assert InventoryService._numeric_or(None, 7) == 7

    assert InventoryService._numeric_or(float("nan"), 7) == 7

    assert InventoryService._numeric_or("12", 7) == 12.0

    assert InventoryService._numeric_or("not-a-number", 7) == 7


def test_store_or_default_handles_blank_and_missing():

    assert InventoryService._store_or_default(None) == "All Stores"

    assert InventoryService._store_or_default(float("nan")) == (
        "All Stores"
    )

    assert InventoryService._store_or_default("  ") == "All Stores"

    assert InventoryService._store_or_default("S1") == "S1"


def test_iter_inventory_rows_none_falls_back_to_forecast_products():

    # No Inventory data at all: every forecasted product still gets a
    # row, with current_stock=None so ReorderService assumes it.
    demand_map = {"P1": {}, "P2": {}}

    rows = InventoryService._iter_inventory_rows(None, demand_map)

    assert {row["product_id"] for row in rows} == {"P1", "P2"}

    assert all(row["current_stock"] is None for row in rows)

    assert all(row["store_id"] == "All Stores" for row in rows)


def test_iter_inventory_rows_missing_current_stock_column():

    # Inventory file exists (has Product ID) but no Current Stock
    # column was ever mapped - every row must still surface with
    # current_stock=None, not be dropped.
    inventory = pd.DataFrame({"Product ID": ["P1", "P2"]})

    rows = InventoryService._iter_inventory_rows(inventory, {})

    assert len(rows) == 2

    assert all(row["current_stock"] is None for row in rows)


def test_iter_inventory_rows_blank_cell_is_none_real_value_kept():

    inventory = pd.DataFrame({

        "Product ID": ["P1", "P2"],

        "Current Stock": [50.0, None]

    })

    rows = {

        row["product_id"]: row

        for row in InventoryService._iter_inventory_rows(inventory, {})

    }

    assert rows["P1"]["current_stock"] == 50.0

    assert rows["P2"]["current_stock"] is None


def test_iter_inventory_rows_adds_forecast_only_products():

    # A product with a forecast but no Inventory row at all must be
    # included (assumed), not silently excluded.
    inventory = pd.DataFrame({

        "Product ID": ["P1"],

        "Current Stock": [50.0]

    })

    demand_map = {"P1": {}, "P2": {}}

    rows = {

        row["product_id"]: row

        for row in InventoryService._iter_inventory_rows(
            inventory,
            demand_map
        )

    }

    assert rows["P1"]["current_stock"] == 50.0

    assert rows["P2"]["current_stock"] is None

    assert rows["P2"]["store_id"] == "All Stores"


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
