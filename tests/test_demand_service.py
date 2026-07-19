"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_demand_service.py

Description :
Unit tests for the Phase 2A demand preparation logic (aggregation,
revenue derivation, split-file merging, gap filling, filters).
Pure DataFrame tests - no database access.

Run with either:
    python tests/test_demand_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from services.demand_service import DemandService
from services.merge_service import MergeService


def sample_sales():

    return pd.DataFrame({

        "Transaction Date": [
            "2026-01-01", "2026-01-01", "2026-01-03",
            "2026-02-10", None
        ],

        "Product ID": ["P1", "P2", "P1", "P2", "P1"],

        "Store ID": ["S1", "S1", "S2", "S2", "S1"],

        "Quantity": [2, 1, 3, 4, 5],

        "Revenue": [20.0, 15.0, 30.0, 60.0, 50.0]

    })


def sample_products():

    return pd.DataFrame({

        "Product ID": ["P1", "P2"],

        "Product Name": ["Chair", "Table"],

        "Category": ["Furniture", "Furniture"],

        "Selling Price": [10.0, 15.0]

    })


# ---------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------

def test_daily_aggregation_fills_gaps():

    series, notes = DemandService._aggregate(
        sample_sales(), "Daily", "Quantity"
    )

    # 2026-01-01 .. 2026-02-10 inclusive = 41 continuous days
    assert len(series) == 41

    assert series.loc["2026-01-01", "Quantity"] == 3

    assert series.loc["2026-01-02", "Quantity"] == 0

    assert series.loc["2026-02-10", "Quantity"] == 4

    # Null-date row excluded and reported
    assert any("missing/invalid dates" in note for note in notes)


def test_monthly_aggregation():

    series, _ = DemandService._aggregate(
        sample_sales(), "Monthly", "Revenue"
    )

    assert len(series) == 2

    assert series.iloc[0]["Revenue"] == 65.0

    assert series.iloc[1]["Revenue"] == 60.0


def test_weekly_aggregation_labels_period_start():

    series, _ = DemandService._aggregate(
        sample_sales(), "Weekly", "Quantity"
    )

    # Every index label must be a Monday (weekday 0)
    assert all(day.weekday() == 0 for day in series.index)

    assert series["Quantity"].sum() == 10


def test_aggregate_requires_date_field():

    frame = sample_sales().drop(columns=["Transaction Date"])

    try:

        DemandService._aggregate(frame, "Daily", "Quantity")

        raise AssertionError("Expected ValueError")

    except ValueError as error:

        assert "Transaction Date" in str(error)


# ---------------------------------------------------------------------
# Revenue derivation
# ---------------------------------------------------------------------

def test_revenue_kept_when_present():

    sales, notes = DemandService._ensure_revenue(
        sample_sales(), sample_products()
    )

    assert notes == []

    assert sales["Revenue"].tolist()[0] == 20.0


def test_revenue_derived_from_selling_price():

    sales = sample_sales().drop(columns=["Revenue"])

    sales, notes = DemandService._ensure_revenue(
        sales, sample_products()
    )

    # P1: 2 x 10, P2: 1 x 15, P1: 3 x 10, P2: 4 x 15, P1: 5 x 10
    assert sales["Revenue"].tolist() == [20.0, 15.0, 30.0, 60.0, 50.0]

    assert any("derived" in note for note in notes)


def test_revenue_underivable_raises():

    sales = sample_sales().drop(columns=["Revenue"])

    try:

        DemandService._ensure_revenue(sales, None)

        raise AssertionError("Expected ValueError")

    except ValueError as error:

        assert "Quantity measure" in str(error)


# ---------------------------------------------------------------------
# Split-file merge
# ---------------------------------------------------------------------

def test_single_frame_passthrough():

    frame = sample_sales()

    merged, notes = MergeService.merge_sales_frames([frame])

    assert merged is frame

    assert notes == []


def test_split_files_merge_on_order_id():

    order_lines = pd.DataFrame({

        "Order ID": ["1", "1", "2"],

        "Product ID": ["P1", "P2", "P1"],

        "Quantity": [2, 1, 4]

    })

    order_headers = pd.DataFrame({

        "Order ID": ["1", "2"],

        "Transaction Date": ["2026-01-05", "2026-01-06"]

    })

    merged, notes = MergeService.merge_sales_frames(
        [order_headers, order_lines]
    )

    assert len(merged) == 3

    assert "Transaction Date" in merged.columns

    assert (

        merged.loc[merged["Order ID"] == "1", "Transaction Date"]

        .tolist() == ["2026-01-05", "2026-01-05"]

    )

    assert any("joined" in note for note in notes)


def test_merge_without_date_source_raises():

    order_lines = pd.DataFrame({

        "Order ID": ["1"],

        "Product ID": ["P1"],

        "Quantity": [2]

    })

    no_date_header = pd.DataFrame({

        "Order ID": ["1"],

        "Customer ID": ["C1"]

    })

    try:

        MergeService.merge_sales_frames(
            [order_lines, no_date_header]
        )

        raise AssertionError("Expected ValueError")

    except ValueError as error:

        assert "Transaction Date" in str(error)


# ---------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------

def test_product_filter():

    sales, notes = DemandService._apply_filters(

        sample_sales(), sample_products(), product_id="P1"

    )

    assert set(sales["Product ID"]) == {"P1"}

    assert len(sales) == 3


def test_store_filter():

    sales, _ = DemandService._apply_filters(

        sample_sales(), sample_products(), store_id="S2"

    )

    assert len(sales) == 2


def test_category_filter():

    sales, _ = DemandService._apply_filters(

        sample_sales(), sample_products(), category="Furniture"

    )

    assert len(sales) == 5

    sales, _ = DemandService._apply_filters(

        sample_sales(), sample_products(), category="Electronics"

    )

    assert len(sales) == 0


def test_category_filter_without_products_raises():

    try:

        DemandService._apply_filters(
            sample_sales(), None, category="Furniture"
        )

        raise AssertionError("Expected ValueError")

    except ValueError as error:

        assert "Products" in str(error)


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
