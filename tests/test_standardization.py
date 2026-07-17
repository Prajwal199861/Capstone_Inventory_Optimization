"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_standardization.py

Description :
Unit tests for the Phase 1 Data Standardization utilities.

Run with either:
    python tests/test_standardization.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from utils.datatype_converter import DatatypeConverter
from utils.dataframe_cleaner import DataFrameCleaner


# ---------------------------------------------------------------------
# DatatypeConverter
# ---------------------------------------------------------------------

def test_field_classification():

    assert DatatypeConverter.is_date_field("Transaction Date")

    assert DatatypeConverter.is_date_field("Date")

    assert not DatatypeConverter.is_date_field("Product ID")

    assert DatatypeConverter.is_numeric_field("Revenue")

    assert DatatypeConverter.is_numeric_field("Current Stock")

    assert not DatatypeConverter.is_numeric_field("Product Name")

    assert DatatypeConverter.is_identifier_field("Store ID")

    assert not DatatypeConverter.is_identifier_field("Discount")


def test_date_conversion():

    series = pd.Series(["2026-01-05", "2026-02-10", None])

    converted, warnings = DatatypeConverter.convert_column(

        series,

        "Transaction Date"

    )

    assert str(converted.dtype).startswith("datetime64")

    assert converted[0].year == 2026

    assert warnings == []


def test_numeric_conversion_with_formatting():

    series = pd.Series(["1,200.50", "₹300", " 45 ", "12"])

    converted, warnings = DatatypeConverter.convert_column(

        series,

        "Revenue"

    )

    assert converted.tolist() == [1200.5, 300.0, 45.0, 12.0]

    assert warnings == []


def test_partial_numeric_failure_warns():

    series = pd.Series(["10", "20", "abc", "30"])

    converted, warnings = DatatypeConverter.convert_column(

        series,

        "Quantity"

    )

    assert converted.isna().sum() == 1

    assert len(warnings) == 1


def test_majority_failure_preserves_original():

    series = pd.Series(["a", "b", "c", "10"])

    converted, warnings = DatatypeConverter.convert_column(

        series,

        "Quantity"

    )

    # More than half failed: original values must be preserved.
    assert converted.tolist() == ["a", "b", "c", "10"]

    assert len(warnings) == 1


def test_identifier_normalized_to_string():

    series = pd.Series([101, 102, 103])

    converted, _ = DatatypeConverter.convert_column(

        series,

        "Product ID"

    )

    assert converted.tolist() == ["101", "102", "103"]


# ---------------------------------------------------------------------
# DataFrameCleaner
# ---------------------------------------------------------------------

def test_clean_trims_and_converts():

    dataframe = pd.DataFrame({

        "Product ID": ["  P1 ", "P2"],

        "Product Name": ["  Chair ", "Table"],

        "Selling Price": ["1,000", "2000"]

    })

    clean, warnings = DataFrameCleaner.clean(

        dataframe,

        "Products"

    )

    assert clean["Product ID"].tolist() == ["P1", "P2"]

    assert clean["Product Name"].tolist() == ["Chair", "Table"]

    assert clean["Selling Price"].tolist() == [1000.0, 2000.0]


def test_clean_deduplicates_master_data():

    dataframe = pd.DataFrame({

        "Product ID": ["P1", "P1", "P2"],

        "Product Name": ["Chair", "Chair", "Table"]

    })

    clean, warnings = DataFrameCleaner.clean(

        dataframe,

        "Products"

    )

    assert len(clean) == 2

    assert any("duplicate" in warning for warning in warnings)


def test_clean_keeps_sales_duplicates():

    dataframe = pd.DataFrame({

        "Product ID": ["P1", "P1"],

        "Quantity": [1, 1],

        "Revenue": [10.0, 10.0]

    })

    clean, warnings = DataFrameCleaner.clean(

        dataframe,

        "Sales"

    )

    # Repeat transactions are legitimate: rows kept, warning raised.
    assert len(clean) == 2

    assert any("duplicate" in warning for warning in warnings)


def test_clean_drops_empty_rows_and_reports_missing():

    dataframe = pd.DataFrame({

        "Product ID": ["P1", None, "P2"],

        "Quantity": [5, None, None]

    })

    clean, warnings = DataFrameCleaner.clean(

        dataframe,

        "Sales"

    )

    assert len(clean) == 2

    assert any("empty row" in warning for warning in warnings)

    assert any("missing value" in warning for warning in warnings)


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

        except AssertionError:

            failures += 1

            print(f"FAIL  {name}")

    print(

        f"\n{len(tests) - failures}/{len(tests)} tests passed."

    )

    sys.exit(1 if failures else 0)
