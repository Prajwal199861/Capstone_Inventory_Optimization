"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : product_service.py

Description :
Milestone 4 - Phase 2: Product Intelligence (Product 360 Dashboard).

Aggregates the existing Forecast, Inventory Optimization and Demand
engines into one Product DTO per the handover spec - it introduces NO
new business calculations. Every number here already exists in
InventoryService's recommendation output, the persisted batch
Forecast, or DemandService's demand series; this module only joins,
filters and rolls per-(product, store) rows up to per-product rows.

load_dataset() is the one expensive pass (reads standardized data,
joins with the persisted forecast, runs the reorder/risk calculations
via InventoryService - exactly what the Inventory page already does).
list_products() and get_product_detail() are cheap, pure functions
over that already-loaded bundle, so a caller (the Streamlit page) can
cache the bundle once per dataset and reuse it across every rerun
(search typing, row selection) without re-triggering the expensive
pass or ever re-running forecasting/optimization itself.
=============================================================================
"""

import pandas as pd

from services.demand_service import DemandService
from services.forecast_service import ForecastService
from services.inventory_service import InventoryService

from services.stock_risk_service import StockRiskService


_RISK_ORDER = {

    level: position

    for position, level in enumerate(StockRiskService.RISK_LEVELS)

}

PRODUCT_TABLE_COLUMNS = [

    "Product ID",

    "Product Name",

    "Category",

    "Current Stock",

    "Forecast Demand",

    "Risk Level",

    "Status"

]


class ProductService:

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @staticmethod
    def load_dataset(
            dataset_id: int
    ) -> dict:
        """
        The one expensive pass for the Products page. Returns plain
        DataFrames/dicts only (no ORM objects) so the result is safe
        to cache across Streamlit reruns.

        Returns:

            {
                "recommendations": DataFrame (InventoryService's full
                    per-product-per-store output),
                "forecast_meta": {
                    "model_name", "granularity", "horizon", "measure",
                    "created_at"
                } | None,
                "forecast_points": DataFrame [Product ID, Period,
                    Forecast, Lower, Upper] - every product's saved
                    batch forecast points, filtered per-product by
                    get_product_detail(),
                "notes": [str]
            }

        Raises ValueError only when InventoryService does (no saved
        batch forecast for this dataset) - the one true precondition,
        identical to the existing Inventory page.
        """

        result = InventoryService.generate_recommendations(dataset_id)

        forecast = ForecastService.get_latest_batch_forecast(
            dataset_id
        )

        forecast_meta = None

        forecast_points = pd.DataFrame(

            columns=["Product ID", "Period", "Forecast", "Lower", "Upper"]

        )

        if forecast is not None:

            forecast_meta = {

                "model_name": forecast.model_name,

                "granularity": forecast.granularity,

                "horizon": forecast.horizon,

                "measure": forecast.measure,

                "created_at": forecast.created_at

            }

            points = [

                {

                    "Product ID": point.product_id,

                    "Period": point.period_date,

                    "Forecast": point.value,

                    "Lower": point.lower,

                    "Upper": point.upper

                }

                for point in forecast.points

                if point.product_id is not None

            ]

            if points:

                forecast_points = pd.DataFrame(points)

        return {

            "recommendations": result["recommendations"],

            "forecast_meta": forecast_meta,

            "forecast_points": forecast_points,

            "notes": result["notes"]

        }

    @staticmethod
    def list_products(
            bundle: dict
    ) -> pd.DataFrame:
        """
        Requirement 1's product table: one row per product (Product
        ID, Product Name, Category, Current Stock, Forecast Demand,
        Risk Level, Status), rolled up from InventoryService's
        per-(product, store) rows - Current Stock summed across
        stores, Risk Level/Status taken from the most severe store.
        """

        recommendations = bundle["recommendations"]

        if recommendations.empty:

            return pd.DataFrame(columns=PRODUCT_TABLE_COLUMNS)

        rows = [

            ProductService._aggregate_store_rows(group)

            for _, group in recommendations.groupby(
                "Product ID",
                sort=False
            )

        ]

        return pd.DataFrame(rows)[PRODUCT_TABLE_COLUMNS]

    @staticmethod
    def get_product_detail(
            bundle: dict,
            dataset_id: int,
            product_id: str
    ) -> dict:
        """
        Requirements 4-10: everything the Product Detail view needs
        for one product.

        Returns:

            {
                "product": dict (Requirement 4 fields, aggregated
                    across stores - see _aggregate_store_rows),
                "stores": DataFrame (Requirement 7 - one row per
                    store this product exists in; a single synthetic
                    "All Stores" row when the dataset carries no
                    Store ID),
                "forecast": {
                    "model_name", "granularity", "horizon", "measure",
                    "created_at", "total", "lower_total", "upper_total",
                    "points": DataFrame [Period, Forecast, Lower, Upper]
                } | None - None means "Forecast not available" for
                    this product (Error Handling requirement),
                "history": DataFrame [Period, <measure>] | None -
                    None means the historical series could not be
                    rebuilt (reported via "notes", never blocks the
                    rest of the page),
                "notes": [str]
            }

        Raises ValueError only if the product has no rows at all in
        this dataset's recommendations (should not happen for a
        product_id sourced from list_products() on the same bundle).
        """

        recommendations = bundle["recommendations"]

        store_rows = recommendations[

            recommendations["Product ID"] == product_id

        ].reset_index(drop=True)

        if store_rows.empty:

            raise ValueError(

                f"Product {product_id} was not found in this "

                f"dataset's recommendations."

            )

        product = ProductService._aggregate_store_rows(store_rows)

        forecast, forecast_notes = ProductService._product_forecast(

            bundle,

            product_id

        )

        history, history_notes = ProductService._product_history(

            dataset_id,

            product_id,

            bundle["forecast_meta"]

        )

        return {

            "product": product,

            "stores": store_rows,

            "forecast": forecast,

            "history": history,

            "notes": forecast_notes + history_notes

        }

    # -----------------------------------------------------------------
    # Internal steps
    # -----------------------------------------------------------------

    @staticmethod
    def _aggregate_store_rows(
            store_rows: pd.DataFrame
    ) -> dict:
        """
        Rolls per-(product, store) rows up to one product-level dict.
        Fields that are identical across every store row for a
        product (Product Name, Category, Season, Price, Forecast
        Demand, Demand Change %) are taken once; per-store inventory
        positions are summed (Current Stock, Safety Stock, Reorder
        Point, Target Stock Level, Recommended Quantity, Inventory
        Value); Days Remaining takes the most urgent (minimum) store;
        Risk Level/Status/Reason/Lead Time are taken from whichever
        store is currently most severe, since a single product-level
        badge should reflect the store that needs attention most.
        """

        worst = store_rows.loc[

            store_rows["Risk Level"]

            .map(_RISK_ORDER)

            .idxmin()

        ]

        return {

            "Product ID": worst["Product ID"],

            "Product Name": worst["Product Name"],

            "Category": worst["Category"],

            "Season": worst["Season"],

            "Price": worst["Price"],

            "Store Count": len(store_rows),

            "Store ID": (

                store_rows["Store ID"].iloc[0]

                if len(store_rows) == 1

                else "All Stores"

            ),

            "Current Stock": round(
                float(store_rows["Current Stock"].sum()), 2
            ),

            "Stock Basis": (

                "Mixed"

                if store_rows["Stock Basis"].nunique() > 1

                else store_rows["Stock Basis"].iloc[0]

            ),

            "Forecast Demand": worst["Forecast Demand"],

            "Demand Change %": worst["Demand Change %"],

            "Target Stock Level": round(
                float(store_rows["Target Stock Level"].sum()), 2
            ),

            "Daily Avg Demand": worst["Daily Avg Demand"],

            "Safety Stock": round(
                float(store_rows["Safety Stock"].sum()), 2
            ),

            "Reorder Point": round(
                float(store_rows["Reorder Point"].sum()), 2
            ),

            "Recommended Quantity": round(
                float(store_rows["Recommended Quantity"].sum()), 2
            ),

            "Days Remaining": (

                round(float(store_rows["Days Remaining"].min()), 1)

                if store_rows["Days Remaining"].notna().any()

                else None

            ),

            "Lead Time (Days)": worst["Lead Time (Days)"],

            "Inventory Value": (

                round(float(store_rows["Inventory Value"].sum()), 2)

                if store_rows["Inventory Value"].notna().any()

                else None

            ),

            "Risk Level": worst["Risk Level"],

            "Status": worst["Status"],

            "Reason": worst["Reason"],

            "Recommendation Timestamp": worst["Recommendation Timestamp"]

        }

    @staticmethod
    def _product_forecast(
            bundle: dict,
            product_id: str
    ):
        """One product's slice of the already-loaded batch forecast
        points, plus the run's metadata. (None, [note]) when this
        product has no forecast points - a product the batch skipped
        for insufficient history, handled per the Error Handling
        requirement rather than treated as a failure."""

        meta = bundle["forecast_meta"]

        all_points = bundle["forecast_points"]

        if meta is None:

            return None, []

        points = (

            all_points[all_points["Product ID"] == product_id]

            .sort_values("Period")

            .reset_index(drop=True)

        )

        if points.empty:

            return None, [

                "Forecast not available for this product (it was "

                "skipped in the last batch run, likely for "

                "insufficient sales history)."

            ]

        has_bounds = points["Lower"].notna().all() and (
            points["Upper"].notna().all()
        )

        return {

            **meta,

            "total": round(float(points["Forecast"].sum()), 2),

            "lower_total": (

                round(float(points["Lower"].sum()), 2)

                if has_bounds

                else None

            ),

            "upper_total": (

                round(float(points["Upper"].sum()), 2)

                if has_bounds

                else None

            ),

            "points": points

        }, []

    @staticmethod
    def _product_history(
            dataset_id: int,
            product_id: str,
            forecast_meta: dict | None
    ):
        """This product's historical demand series, at the same
        granularity/measure as the batch forecast so the two overlay
        correctly on the trend chart. (None, [note]) rather than
        raising - a missing history never blocks the rest of the
        detail view."""

        granularity = (
            forecast_meta["granularity"] if forecast_meta else "Monthly"
        )

        measure = (
            forecast_meta["measure"] if forecast_meta else "Quantity"
        )

        try:

            demand = DemandService.build_demand_series(

                dataset_id,

                granularity=granularity,

                measure=measure,

                product_id=product_id

            )

        except ValueError as error:

            return None, [f"Historical trend unavailable: {error}"]

        series = demand["series"]

        if series.empty:

            return None, [

                "Historical trend unavailable: no sales history for "

                "this product."

            ]

        return series, []
