"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_product_service.py

Description :
Unit tests for the Milestone 4 - Phase 2 Product Intelligence
aggregation (services/product_service.py). Pure logic against
synthetic "bundle" dicts shaped exactly like ProductService.
load_dataset() returns - no database access, matching how
InventoryService/ReorderService/StockRiskService are already tested
in this project.

Run with either:
    python tests/test_product_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from services.product_service import PRODUCT_TABLE_COLUMNS, ProductService


TIMESTAMP = datetime(2026, 1, 1, 12, 0, 0)


def _row(**overrides):

    base = {

        "Product ID": "P1",

        "Product Name": "Widget",

        "Category": "Tools",

        "Season": None,

        "Price": 9.99,

        "Store ID": "S1",

        "Current Stock": 10.0,

        "Stock Basis": "Actual",

        "Forecast Demand": 100.0,

        "Demand Change %": 5.0,

        "Target Stock Level": 50.0,

        "Daily Avg Demand": 3.3,

        "Safety Stock": 15.0,

        "Reorder Point": 25.0,

        "Recommended Quantity": 40.0,

        "Days Remaining": 3.0,

        "Lead Time (Days)": 7,

        "Inventory Value": 99.9,

        "Risk Level": "Critical",

        "Status": "Reorder Required",

        "Reason": "Store 1 critical",

        "Recommendation Timestamp": TIMESTAMP

    }

    base.update(overrides)

    return base


def test_aggregate_single_store_row_is_a_passthrough():

    rows = pd.DataFrame([_row()])

    aggregated = ProductService.aggregate_store_rows(rows)

    assert aggregated["Store ID"] == "S1"

    assert aggregated["Store Count"] == 1

    assert aggregated["Current Stock"] == 10.0

    assert aggregated["Stock Basis"] == "Actual"


def test_aggregate_sums_inventory_positions_across_stores():

    rows = pd.DataFrame([

        _row(**{
            "Store ID": "S1",
            "Current Stock": 10.0,
            "Safety Stock": 15.0,
            "Recommended Quantity": 40.0,
            "Inventory Value": 99.9
        }),

        _row(**{

            "Store ID": "S2",

            "Current Stock": 90.0,

            "Safety Stock": 15.0,

            "Recommended Quantity": 0.0,

            "Inventory Value": 899.1,

            "Risk Level": "Low",

            "Status": "Adequate",

            "Reason": "Store 2 fine",

            "Days Remaining": 27.0

        })

    ])

    aggregated = ProductService.aggregate_store_rows(rows)

    assert aggregated["Store Count"] == 2

    assert aggregated["Store ID"] == "All Stores"

    assert aggregated["Current Stock"] == 100.0

    assert aggregated["Safety Stock"] == 30.0

    assert aggregated["Recommended Quantity"] == 40.0

    assert aggregated["Inventory Value"] == 999.0


def test_aggregate_picks_most_severe_risk_and_min_days_remaining():

    rows = pd.DataFrame([

        _row(**{
            "Store ID": "S1",
            "Risk Level": "Low",
            "Status": "Adequate",
            "Days Remaining": 27.0
        }),

        _row(**{
            "Store ID": "S2",
            "Risk Level": "Critical",
            "Status": "Reorder Required",
            "Reason": "Store 2 urgent",
            "Days Remaining": 2.0
        })

    ])

    aggregated = ProductService.aggregate_store_rows(rows)

    assert aggregated["Risk Level"] == "Critical"

    assert aggregated["Status"] == "Reorder Required"

    assert aggregated["Reason"] == "Store 2 urgent"

    assert aggregated["Days Remaining"] == 2.0


def test_aggregate_flags_mixed_stock_basis():

    rows = pd.DataFrame([

        _row(**{"Store ID": "S1", "Stock Basis": "Actual"}),

        _row(**{"Store ID": "S2", "Stock Basis": "Assumed"})

    ])

    aggregated = ProductService.aggregate_store_rows(rows)

    assert aggregated["Stock Basis"] == "Mixed"


def test_list_products_returns_expected_columns_and_one_row_per_product():

    recommendations = pd.DataFrame([

        _row(**{"Product ID": "P1", "Store ID": "S1"}),

        _row(**{"Product ID": "P1", "Store ID": "S2"}),

        _row(**{

            "Product ID": "P2",
            "Product Name": "Gadget",
            "Store ID": "S1",
            "Risk Level": "Low",
            "Status": "Adequate"

        })

    ])

    bundle = {"recommendations": recommendations}

    table = ProductService.list_products(bundle)

    assert list(table.columns) == PRODUCT_TABLE_COLUMNS

    assert len(table) == 2

    p1 = table[table["Product ID"] == "P1"].iloc[0]

    assert p1["Current Stock"] == 20.0  # 10 + 10 across two stores


def test_list_products_empty_recommendations_returns_empty_frame():

    bundle = {"recommendations": pd.DataFrame()}

    table = ProductService.list_products(bundle)

    assert table.empty

    assert list(table.columns) == PRODUCT_TABLE_COLUMNS


def test_product_forecast_none_when_no_batch_forecast():

    forecast, notes = ProductService._product_forecast(

        {"forecast_meta": None, "forecast_points": pd.DataFrame()},

        "P1"

    )

    assert forecast is None

    assert notes == []


def test_product_forecast_none_with_note_when_product_has_no_points():

    bundle = {

        "forecast_meta": {

            "model_name": "Auto (per product)",

            "granularity": "Monthly",

            "horizon": 3,

            "measure": "Quantity",

            "created_at": TIMESTAMP

        },

        "forecast_points": pd.DataFrame(

            columns=["Product ID", "Period", "Forecast", "Lower", "Upper"]

        )

    }

    forecast, notes = ProductService._product_forecast(bundle, "P1")

    assert forecast is None

    assert len(notes) == 1

    assert "not available" in notes[0]


def test_product_forecast_aggregates_points_for_the_product():

    points = pd.DataFrame([

        {
            "Product ID": "P1", "Period": datetime(2026, 1, 1),
            "Forecast": 30.0, "Lower": 20.0, "Upper": 40.0
        },

        {
            "Product ID": "P1", "Period": datetime(2026, 2, 1),
            "Forecast": 40.0, "Lower": 25.0, "Upper": 55.0
        },

        {
            "Product ID": "P2", "Period": datetime(2026, 1, 1),
            "Forecast": 999.0, "Lower": 900.0, "Upper": 1000.0
        }

    ])

    bundle = {

        "forecast_meta": {

            "model_name": "Auto (per product)",

            "granularity": "Monthly",

            "horizon": 2,

            "measure": "Quantity",

            "created_at": TIMESTAMP

        },

        "forecast_points": points

    }

    forecast, notes = ProductService._product_forecast(bundle, "P1")

    assert notes == []

    assert forecast["total"] == 70.0

    assert forecast["lower_total"] == 45.0

    assert forecast["upper_total"] == 95.0

    assert len(forecast["points"]) == 2

    assert "P2" not in forecast["points"]["Product ID"].values


def test_get_product_detail_raises_for_unknown_product():

    bundle = {

        "recommendations": pd.DataFrame([_row()]),

        "forecast_meta": None,

        "forecast_points": pd.DataFrame()

    }

    try:

        ProductService.get_product_detail(bundle, 1, "does-not-exist")

        assert False, "expected ValueError"

    except ValueError:

        pass


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
