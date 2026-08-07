"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : report_service.py

Description :
Milestone 4 - Phase 3: Reports & Business Intelligence.

Consolidates Forecasting, Inventory Optimization, Product Intelligence
and AI Recommendations into report DTOs for pages/reports.py. This
module introduces NO new forecasting or optimization calculations -
every figure here already exists in InventoryService's recommendation
output, the persisted batch Forecast, DemandService's demand series,
or ProductService's per-product rollup; this module only aggregates,
filters and reshapes them for reporting.

load_dataset() is the one expensive pass (delegates to ProductService.
load_dataset, which itself never re-runs forecasting/optimization -
it only reads what is already persisted). Every other method here is
a cheap, pure function over that already-loaded bundle.
=============================================================================
"""

import pandas as pd

from services.demand_service import DemandService
from services.product_service import ProductService
from services.stock_risk_service import StockRiskService

from utils.inventory_metrics import InventoryMetrics


TOP_N_DEFAULT = 10

CATEGORY_FALLBACK = "Uncategorized"


class ReportService:

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @staticmethod
    def load_dataset(
            dataset_id: int
    ) -> dict:
        """
        The one expensive pass, shared by every report category.
        Returns plain DataFrames/dicts only (no ORM objects) so it is
        safe to cache across Streamlit reruns.

        Returns:

            {
                "recommendations": DataFrame (InventoryService's full
                    per-product-per-store output),
                "products": DataFrame (one row per product, every
                    field ProductService.aggregate_store_rows
                    produces - richer than ProductService.
                    list_products()'s 7-column summary table),
                "forecast_meta": {
                    "model_name", "granularity", "horizon", "measure",
                    "created_at"
                } | None,
                "forecast_points": DataFrame [Product ID, Period,
                    Forecast, Lower, Upper],
                "notes": [str]
            }

        Raises ValueError only when there is no saved batch forecast
        for this dataset (the same precondition every other report-
        adjacent page already enforces).
        """

        bundle = ProductService.load_dataset(dataset_id)

        recommendations = bundle["recommendations"]

        products = ReportService._products_table(recommendations)

        return {

            "recommendations": recommendations,

            "products": products,

            "forecast_meta": bundle["forecast_meta"],

            "forecast_points": bundle["forecast_points"],

            "notes": bundle["notes"]

        }

    # -----------------------------------------------------------------
    # 1. Executive Dashboard Report
    # -----------------------------------------------------------------

    @staticmethod
    def executive_summary(
            bundle: dict
    ) -> dict:
        """
        Returns:

            {
                "kpis": {
                    "total_products", "forecasted_products",
                    "critical_risk", "high_risk", "inventory_value",
                    "forecast_horizon", "forecast_model"
                },
                "risk_distribution": {"Critical", "High", "Medium",
                    "Low"} -> count,
                "forecast_demand_by_category": DataFrame
                    [Category, Forecast Demand],
                "inventory_value_by_category": DataFrame
                    [Category, Inventory Value],
                "top_products_by_demand": DataFrame
                    [Product Name, Forecast Demand] (top 10)
            }
        """

        recommendations = bundle["recommendations"]

        products = bundle["products"]

        meta = bundle["forecast_meta"]

        risk = InventoryMetrics.risk_breakdown(recommendations)

        kpis = {

            "total_products": int(len(products)),

            "forecasted_products": ReportService._forecasted_product_count(
                bundle["forecast_points"]
            ),

            "critical_risk": risk["Critical"],

            "high_risk": risk["High"],

            "inventory_value": (

                float(products["Inventory Value"].dropna().sum())

                if not products.empty
                and "Inventory Value" in products.columns
                and products["Inventory Value"].notna().any()

                else None

            ),

            "forecast_horizon": meta["horizon"] if meta else None,

            "forecast_model": meta["model_name"] if meta else None

        }

        return {

            "kpis": kpis,

            "risk_distribution": risk,

            "forecast_demand_by_category": ReportService._sum_by_category(
                products, "Forecast Demand"
            ),

            "inventory_value_by_category": ReportService._sum_by_category(
                products, "Inventory Value"
            ),

            "top_products_by_demand": ReportService._top_n(

                products,

                "Forecast Demand",

                ["Product Name", "Forecast Demand"],

                TOP_N_DEFAULT

            )

        }

    # -----------------------------------------------------------------
    # 2. Inventory Report
    # -----------------------------------------------------------------

    @staticmethod
    def inventory_position_totals(
            recommendations: pd.DataFrame
    ) -> dict:
        """{"Current Stock", "Safety Stock", "Reorder Point",
        "Recommended Quantity"} -> summed total, for whatever slice
        of recommendations is passed in (dataset-wide or filtered) -
        the same numbers already on every row, just added up."""

        columns = [

            "Current Stock",

            "Safety Stock",

            "Reorder Point",

            "Recommended Quantity"

        ]

        if recommendations is None or recommendations.empty:

            return {column: 0.0 for column in columns}

        return {

            column: (

                round(float(recommendations[column].dropna().sum()), 2)

                if column in recommendations.columns

                else 0.0

            )

            for column in columns

        }

    # -----------------------------------------------------------------
    # 3. Forecast Report
    # -----------------------------------------------------------------

    @staticmethod
    def forecast_report(
            bundle: dict,
            dataset_id: int
    ) -> dict:
        """
        Returns:

            {
                "meta": {...} | None,
                "products_forecasted": int,
                "confidence_range": (lower_total, upper_total)
                    | (None, None),
                "table": DataFrame [Product ID, Product Name,
                    Forecast, Lower Bound, Upper Bound, MAPE (%),
                    Model Used],
                "trend": DataFrame [Period, Forecast, Lower, Upper]
                    (summed across every product, by period),
                "history": DataFrame [Period, <measure>] | None
                    (dataset-wide historical series),
                "demand_by_product": DataFrame
                    [Product Name, Forecast Demand] (top 15),
                "notes": [str]
            }
        """

        meta = bundle["forecast_meta"]

        points = bundle["forecast_points"]

        products = bundle["products"]

        notes = []

        if meta is None or points.empty:

            return {

                "meta": meta,

                "products_forecasted": 0,

                "confidence_range": (None, None),

                "table": pd.DataFrame(

                    columns=[
                        "Product ID", "Product Name", "Forecast",
                        "Lower Bound", "Upper Bound", "MAPE (%)",
                        "Model Used"
                    ]

                ),

                "trend": pd.DataFrame(
                    columns=["Period", "Forecast", "Lower", "Upper"]
                ),

                "history": None,

                "demand_by_product": pd.DataFrame(),

                "notes": notes

            }

        has_bounds = (

            points["Lower"].notna().all()
            and points["Upper"].notna().all()

        )

        confidence_range = (

            (

                round(float(points["Lower"].sum()), 2),

                round(float(points["Upper"].sum()), 2)

            )

            if has_bounds

            else (None, None)

        )

        # Per-product batch runs persist one dataset-level Forecast
        # record, not per-product accuracy - MAPE genuinely is not
        # available here without re-running a backtest, which this
        # report deliberately avoids (no new forecasting calculations).
        notes.append(

            "MAPE is not available for batch forecast runs - the "

            "batch run persists one dataset-level forecast, not "

            "per-product accuracy metrics."

        )

        table = ReportService._forecast_table(points, products, meta)

        trend = (

            points

            .groupby("Period", as_index=False)

            .agg(

                Forecast=("Forecast", "sum"),

                Lower=("Lower", "sum"),

                Upper=("Upper", "sum")

            )

            .sort_values("Period")

            .reset_index(drop=True)

        )

        history, history_notes = ReportService._dataset_history(
            dataset_id,
            meta
        )

        notes.extend(history_notes)

        return {

            "meta": meta,

            "products_forecasted": int(points["Product ID"].nunique()),

            "confidence_range": confidence_range,

            "table": table,

            "trend": trend,

            "history": history,

            "demand_by_product": ReportService._top_n(

                products,

                "Forecast Demand",

                ["Product Name", "Forecast Demand"],

                15

            ),

            "notes": notes

        }

    # -----------------------------------------------------------------
    # 4. Product Performance Report
    # -----------------------------------------------------------------

    @staticmethod
    def product_performance_report(
            bundle: dict
    ) -> dict:
        """
        Returns:

            {
                "top_growing": DataFrame (Demand Change % > 0,
                    highest first, top 5),
                "top_declining": DataFrame (Demand Change % < 0,
                    lowest first, top 5),
                "highest_inventory_value": DataFrame (top 10),
                "highest_forecast_demand": DataFrame (top 10),
                "critical_products": DataFrame (Risk Level ==
                    "Critical"),
                "category_performance": DataFrame
                    [Category, Forecast Demand],
                "top20_demand": DataFrame
                    [Product Name, Forecast Demand] (top 20, for the
                    chart)
            }
        """

        products = bundle["products"]

        if products.empty:

            empty = pd.DataFrame()

            return {

                "top_growing": empty,

                "top_declining": empty,

                "highest_inventory_value": empty,

                "highest_forecast_demand": empty,

                "critical_products": empty,

                "category_performance": empty,

                "top20_demand": empty

            }

        display_columns = [

            "Product ID",
            "Product Name",
            "Category",
            "Demand Change %",
            "Forecast Demand",
            "Inventory Value",
            "Risk Level",
            "Status"

        ]

        display_columns = [

            column
            for column in display_columns
            if column in products.columns

        ]

        with_change = products.dropna(subset=["Demand Change %"])

        top_growing = (

            with_change[with_change["Demand Change %"] > 0]

            .nlargest(5, "Demand Change %")

            [display_columns]

        )

        top_declining = (

            with_change[with_change["Demand Change %"] < 0]

            .nsmallest(5, "Demand Change %")

            [display_columns]

        )

        return {

            "top_growing": top_growing,

            "top_declining": top_declining,

            "highest_inventory_value": ReportService._top_n(

                products, "Inventory Value", display_columns, 10

            ),

            "highest_forecast_demand": ReportService._top_n(

                products, "Forecast Demand", display_columns, 10

            ),

            "critical_products": products[

                products["Risk Level"] == "Critical"

            ][display_columns],

            "category_performance": ReportService._sum_by_category(
                products, "Forecast Demand"
            ),

            "top20_demand": ReportService._top_n(

                products,

                "Forecast Demand",

                ["Product Name", "Forecast Demand"],

                20

            )

        }

    # -----------------------------------------------------------------
    # 5. AI Executive Report - payload only (the AI call itself is
    # AIRecommendationService.generate_executive_summary())
    # -----------------------------------------------------------------

    @staticmethod
    def ai_executive_payload(
            bundle: dict,
            dataset_name: str
    ) -> dict:
        """Aggregates already-computed figures into the input
        AIRecommendationService.generate_executive_summary() expects.
        No AI call happens here."""

        recommendations = bundle["recommendations"]

        products = bundle["products"]

        meta = bundle["forecast_meta"]

        summary = InventoryMetrics.summarize(recommendations)

        risk = InventoryMetrics.risk_breakdown(recommendations)

        return {

            "dataset_name": dataset_name,

            "total_products": summary["total_products"],

            "forecast_model": meta["model_name"] if meta else None,

            "forecast_granularity": meta["granularity"] if meta else None,

            "forecast_horizon": meta["horizon"] if meta else None,

            "critical_count": risk["Critical"],

            "high_count": risk["High"],

            "medium_count": risk["Medium"],

            "low_count": risk["Low"],

            "reorder_count": summary["products_to_reorder"],

            "overstock_count": summary["overstocked_products"],

            "total_inventory_value": summary["inventory_value"],

            "avg_days_remaining": summary["avg_days_remaining"],

            "top_critical_products": ReportService._named_reason_list(

                products,

                StockRiskService.RISK_LEVELS[0],

                "Risk Level"

            ),

            "top_overstocked_products": ReportService._named_reason_list(

                products,

                StockRiskService.STATUS_OVERSTOCK_WARNING,

                "Status"

            )

        }

    # -----------------------------------------------------------------
    # Combined "full workbook" export (Executive/Forecast/Inventory/
    # Products sheets) - a separate concept from each report
    # category's own per-report export.
    # -----------------------------------------------------------------

    INVENTORY_SHEET_COLUMNS = [

        "Product ID",

        "Product Name",

        "Category",

        "Store ID",

        "Current Stock",

        "Forecast Demand",

        "Safety Stock",

        "Reorder Point",

        "Recommended Quantity",

        "Risk Level",

        "Status",

        "Reason"

    ]

    @staticmethod
    def combined_workbook_sheets(
            bundle: dict,
            dataset_name: str
    ) -> dict:
        """
        {"Executive": DataFrame, "Forecast": DataFrame, "Inventory":
        DataFrame, "Products": DataFrame} - the four sheets the
        handover doc's combined Excel export names. Builds each sheet
        from data already computed elsewhere in this class; no new
        aggregation beyond reshaping into a flat table per sheet.
        """

        exec_summary = ReportService.executive_summary(bundle)

        kpis = exec_summary["kpis"]

        executive_sheet = pd.DataFrame([

            {"Metric": "Dataset", "Value": dataset_name},

            {"Metric": "Total Products", "Value": kpis["total_products"]},

            {

                "Metric": "Forecasted Products",

                "Value": kpis["forecasted_products"]

            },

            {"Metric": "Critical Risk", "Value": kpis["critical_risk"]},

            {"Metric": "High Risk", "Value": kpis["high_risk"]},

            {

                "Metric": "Inventory Value",

                "Value": kpis["inventory_value"]

            },

            {

                "Metric": "Forecast Horizon",

                "Value": kpis["forecast_horizon"]

            },

            {"Metric": "Forecast Model", "Value": kpis["forecast_model"]}

        ])

        forecast_sheet = ReportService._forecast_table(

            bundle["forecast_points"],

            bundle["products"],

            bundle["forecast_meta"]

        )

        recommendations = bundle["recommendations"]

        inventory_columns = [

            column

            for column in ReportService.INVENTORY_SHEET_COLUMNS

            if column in recommendations.columns

        ]

        inventory_sheet = (

            recommendations[inventory_columns]

            if not recommendations.empty

            else pd.DataFrame(columns=inventory_columns)

        )

        return {

            "Executive": executive_sheet,

            "Forecast": forecast_sheet,

            "Inventory": inventory_sheet,

            "Products": bundle["products"]

        }

    # -----------------------------------------------------------------
    # Internal steps
    # -----------------------------------------------------------------

    @staticmethod
    def _forecast_table(
            points: pd.DataFrame,
            products: pd.DataFrame,
            meta: dict | None
    ) -> pd.DataFrame:
        """[Product ID, Product Name, Forecast, Lower Bound, Upper
        Bound, MAPE (%), Model Used] - one row per forecasted product,
        summed across its forecast periods. MAPE is always None (see
        forecast_report's docstring/notes - not available for batch
        runs)."""

        columns = [

            "Product ID", "Product Name", "Forecast",
            "Lower Bound", "Upper Bound", "MAPE (%)", "Model Used"

        ]

        if meta is None or points.empty:

            return pd.DataFrame(columns=columns)

        name_map = (

            products.set_index("Product ID")["Product Name"].to_dict()

            if not products.empty

            else {}

        )

        table = (

            points

            .groupby("Product ID", as_index=False)

            .agg(

                Forecast=("Forecast", "sum"),

                **{"Lower Bound": ("Lower", "sum")},

                **{"Upper Bound": ("Upper", "sum")}

            )

        )

        table["Product Name"] = table["Product ID"].map(
            lambda pid: name_map.get(pid, pid)
        )

        table["MAPE (%)"] = None

        table["Model Used"] = meta["model_name"]

        return (

            table[columns]

            .sort_values("Forecast", ascending=False)

            .reset_index(drop=True)

        )

    @staticmethod
    def _products_table(
            recommendations: pd.DataFrame
    ) -> pd.DataFrame:
        """One row per product, every field aggregate_store_rows
        produces - reused instead of reimplemented, per product_id
        the same rollup ProductService itself uses for the Products
        page."""

        if recommendations.empty:

            return pd.DataFrame()

        return pd.DataFrame([

            ProductService.aggregate_store_rows(group)

            for _, group in recommendations.groupby(
                "Product ID",
                sort=False
            )

        ])

    @staticmethod
    def _forecasted_product_count(
            forecast_points: pd.DataFrame
    ) -> int:

        if forecast_points is None or forecast_points.empty:

            return 0

        return int(forecast_points["Product ID"].nunique())

    @staticmethod
    def _sum_by_category(
            products: pd.DataFrame,
            value_column: str
    ) -> pd.DataFrame:
        """[Category, <value_column>] summed - blank/missing Category
        is grouped as "Uncategorized" rather than silently dropped."""

        if (

                products.empty

                or "Category" not in products.columns

                or value_column not in products.columns

        ):

            return pd.DataFrame(columns=["Category", value_column])

        working = products.copy()

        working["Category"] = (

            working["Category"]

            .fillna(CATEGORY_FALLBACK)

            .replace("", CATEGORY_FALLBACK)

        )

        return (

            working

            .groupby("Category", as_index=False)[value_column]

            .sum()

            .sort_values(value_column, ascending=False)

            .reset_index(drop=True)

        )

    @staticmethod
    def _top_n(
            products: pd.DataFrame,
            sort_column: str,
            columns: list,
            n: int
    ) -> pd.DataFrame:

        if products.empty or sort_column not in products.columns:

            return pd.DataFrame(columns=columns)

        available_columns = [

            column for column in columns if column in products.columns

        ]

        return (

            products

            .dropna(subset=[sort_column])

            .nlargest(n, sort_column)

            [available_columns]

            .reset_index(drop=True)

        )

    @staticmethod
    def _named_reason_list(
            products: pd.DataFrame,
            match_value: str,
            match_column: str,
            limit: int = 5
    ) -> list:
        """[{"name", "detail"}] for the AI prompt - the top `limit`
        products matching `match_value` in `match_column`, using each
        product's already-computed "Reason" as the detail so nothing
        is invented for the AI to summarize."""

        if products.empty or match_column not in products.columns:

            return []

        matched = products[products[match_column] == match_value]

        if matched.empty:

            return []

        if "Days Remaining" in matched.columns:

            matched = matched.sort_values(

                "Days Remaining",

                na_position="last"

            )

        return [

            {

                "name": row.get("Product Name", row.get("Product ID")),

                "detail": row.get("Reason", "No reason recorded")

            }

            for _, row in matched.head(limit).iterrows()

        ]

    @staticmethod
    def _dataset_history(
            dataset_id: int,
            meta: dict
    ):
        """Dataset-wide historical demand series at the same
        granularity/measure as the batch forecast, for the "Forecast
        vs Historical" chart. (None, [note]) rather than raising - a
        missing history never blocks the rest of the report."""

        try:

            demand = DemandService.build_demand_series(

                dataset_id,

                granularity=meta["granularity"],

                measure=meta["measure"]

            )

        except ValueError as error:

            return None, [f"Historical trend unavailable: {error}"]

        series = demand["series"]

        if series.empty:

            return None, ["Historical trend unavailable: no sales history."]

        return series, []
