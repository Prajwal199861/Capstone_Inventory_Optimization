"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_report_service.py

Description :
Unit tests for the Milestone 4 - Phase 3 report aggregation
(services/report_service.py). Pure logic against synthetic bundles
shaped exactly like ReportService.load_dataset() returns - no
database access, matching how ProductService/InventoryService are
already tested in this project.

Run with either:
    python tests/test_report_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from services.report_service import ReportService


TIMESTAMP = datetime(2026, 1, 1, 12, 0, 0)


def _rec_row(**overrides):

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


SAMPLE_RECOMMENDATIONS = pd.DataFrame([

    _rec_row(),

    _rec_row(**{

        "Product ID": "P2",

        "Product Name": "Gadget",

        "Category": "Electronics",

        "Store ID": "S1",

        "Current Stock": 900.0,

        "Forecast Demand": 50.0,

        "Demand Change %": -10.0,

        "Target Stock Level": 100.0,

        "Safety Stock": 20.0,

        "Reorder Point": 30.0,

        "Recommended Quantity": 0.0,

        "Days Remaining": 60.0,

        "Inventory Value": 899.1,

        "Risk Level": "Low",

        "Status": "Overstock Warning",

        "Reason": "Way overstocked"

    })

])

SAMPLE_POINTS = pd.DataFrame([

    {
        "Product ID": "P1", "Period": datetime(2026, 1, 1),
        "Forecast": 50.0, "Lower": 40.0, "Upper": 60.0
    },

    {
        "Product ID": "P2", "Period": datetime(2026, 1, 1),
        "Forecast": 25.0, "Lower": 20.0, "Upper": 30.0
    }

])

SAMPLE_META = {

    "model_name": "Auto (per product)",

    "granularity": "Monthly",

    "horizon": 2,

    "measure": "Quantity",

    "created_at": TIMESTAMP

}


def sample_bundle():

    return {

        "recommendations": SAMPLE_RECOMMENDATIONS.copy(),

        "products": ReportService._products_table(SAMPLE_RECOMMENDATIONS),

        "forecast_meta": dict(SAMPLE_META),

        "forecast_points": SAMPLE_POINTS.copy(),

        "notes": []

    }


# ---------------------------------------------------------------------
# Executive Dashboard
# ---------------------------------------------------------------------

def test_executive_summary_kpis():

    data = ReportService.executive_summary(sample_bundle())

    kpis = data["kpis"]

    assert kpis["total_products"] == 2

    assert kpis["forecasted_products"] == 2

    assert kpis["critical_risk"] == 1

    assert kpis["high_risk"] == 0

    assert kpis["inventory_value"] == 999.0

    assert kpis["forecast_horizon"] == 2

    assert kpis["forecast_model"] == "Auto (per product)"


def test_executive_summary_risk_distribution():

    data = ReportService.executive_summary(sample_bundle())

    assert data["risk_distribution"] == {

        "Critical": 1, "High": 0, "Medium": 0, "Low": 1

    }


def test_executive_summary_category_breakdowns_never_drop_uncategorized():

    bundle = sample_bundle()

    bundle["products"].loc[0, "Category"] = None

    data = ReportService.executive_summary(bundle)

    categories = set(data["forecast_demand_by_category"]["Category"])

    assert "Uncategorized" in categories

    assert len(data["forecast_demand_by_category"]) == 2


def test_executive_summary_top_products_sorted_descending():

    data = ReportService.executive_summary(sample_bundle())

    top = data["top_products_by_demand"]

    assert list(top["Product Name"]) == ["Widget", "Gadget"]


def test_executive_summary_empty_dataset_does_not_raise():

    bundle = {

        "recommendations": pd.DataFrame(),

        "products": pd.DataFrame(),

        "forecast_meta": None,

        "forecast_points": pd.DataFrame(),

        "notes": []

    }

    data = ReportService.executive_summary(bundle)

    assert data["kpis"]["total_products"] == 0

    assert data["kpis"]["forecast_model"] is None


# ---------------------------------------------------------------------
# Inventory Report
# ---------------------------------------------------------------------

def test_inventory_position_totals_sums_across_rows():

    totals = ReportService.inventory_position_totals(
        SAMPLE_RECOMMENDATIONS
    )

    assert totals["Current Stock"] == 910.0

    assert totals["Safety Stock"] == 35.0

    assert totals["Reorder Point"] == 55.0

    assert totals["Recommended Quantity"] == 40.0


def test_inventory_position_totals_empty_returns_zeros():

    totals = ReportService.inventory_position_totals(pd.DataFrame())

    assert totals["Current Stock"] == 0.0


# ---------------------------------------------------------------------
# Forecast Report
# ---------------------------------------------------------------------

def test_forecast_report_table_and_trend():

    data = ReportService.forecast_report(sample_bundle(), dataset_id=999)

    assert data["products_forecasted"] == 2

    assert data["confidence_range"] == (60.0, 90.0)

    assert len(data["table"]) == 2

    assert set(data["table"]["Product ID"]) == {"P1", "P2"}

    assert data["table"]["MAPE (%)"].isna().all()

    assert any("MAPE" in note for note in data["notes"])

    assert len(data["trend"]) == 1  # both products share one period

    assert data["trend"].iloc[0]["Forecast"] == 75.0


def test_forecast_report_no_forecast_meta_returns_empty_shapes():

    bundle = sample_bundle()

    bundle["forecast_meta"] = None

    bundle["forecast_points"] = pd.DataFrame()

    data = ReportService.forecast_report(bundle, dataset_id=999)

    assert data["meta"] is None

    assert data["products_forecasted"] == 0

    assert data["table"].empty

    assert data["history"] is None


def test_forecast_report_history_unavailable_is_a_note_not_a_raise():

    data = ReportService.forecast_report(sample_bundle(), dataset_id=999)

    assert data["history"] is None

    assert any(

        "Historical trend unavailable" in note

        for note in data["notes"]

    )


# ---------------------------------------------------------------------
# Product Performance Report
# ---------------------------------------------------------------------

def test_product_performance_top_growing_and_declining():

    data = ReportService.product_performance_report(sample_bundle())

    assert list(data["top_growing"]["Product ID"]) == ["P1"]

    assert list(data["top_declining"]["Product ID"]) == ["P2"]


def test_product_performance_critical_products():

    data = ReportService.product_performance_report(sample_bundle())

    assert list(data["critical_products"]["Product ID"]) == ["P1"]


def test_product_performance_highest_inventory_value_sorted_desc():

    data = ReportService.product_performance_report(sample_bundle())

    assert list(
        data["highest_inventory_value"]["Product ID"]
    ) == ["P2", "P1"]


def test_product_performance_empty_products_returns_empty_frames():

    bundle = {

        "recommendations": pd.DataFrame(),

        "products": pd.DataFrame(),

        "forecast_meta": None,

        "forecast_points": pd.DataFrame(),

        "notes": []

    }

    data = ReportService.product_performance_report(bundle)

    assert data["top_growing"].empty

    assert data["critical_products"].empty


# ---------------------------------------------------------------------
# AI Executive Report payload
# ---------------------------------------------------------------------

def test_ai_executive_payload_aggregates_correctly():

    payload = ReportService.ai_executive_payload(
        sample_bundle(),
        "Demo Dataset"
    )

    assert payload["dataset_name"] == "Demo Dataset"

    assert payload["total_products"] == 2

    assert payload["critical_count"] == 1

    assert payload["overstock_count"] == 1

    assert payload["total_inventory_value"] == 999.0


def test_ai_executive_payload_top_critical_products_uses_real_reason():

    payload = ReportService.ai_executive_payload(
        sample_bundle(),
        "Demo Dataset"
    )

    assert payload["top_critical_products"] == [

        {"name": "Widget", "detail": "Store 1 critical"}

    ]


def test_ai_executive_payload_top_overstocked_products():

    payload = ReportService.ai_executive_payload(
        sample_bundle(),
        "Demo Dataset"
    )

    assert payload["top_overstocked_products"] == [

        {"name": "Gadget", "detail": "Way overstocked"}

    ]


def test_ai_executive_payload_no_critical_products_is_empty_list():

    bundle = sample_bundle()

    bundle["products"]["Risk Level"] = "Low"

    payload = ReportService.ai_executive_payload(bundle, "Demo Dataset")

    assert payload["top_critical_products"] == []


# ---------------------------------------------------------------------
# Combined workbook
# ---------------------------------------------------------------------

def test_combined_workbook_has_all_four_sheets():

    sheets = ReportService.combined_workbook_sheets(
        sample_bundle(),
        "Demo Dataset"
    )

    assert set(sheets.keys()) == {

        "Executive", "Forecast", "Inventory", "Products"

    }

    assert len(sheets["Forecast"]) == 2

    assert len(sheets["Products"]) == 2

    assert len(sheets["Inventory"]) == 2


def test_combined_workbook_executive_sheet_includes_dataset_name():

    sheets = ReportService.combined_workbook_sheets(
        sample_bundle(),
        "Demo Dataset"
    )

    executive = sheets["Executive"]

    dataset_row = executive[executive["Metric"] == "Dataset"]

    assert dataset_row.iloc[0]["Value"] == "Demo Dataset"


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
