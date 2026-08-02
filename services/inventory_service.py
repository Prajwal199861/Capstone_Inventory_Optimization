"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : inventory_service.py

Description :
Milestone 3 - Phase 3: Inventory Optimization Engine.

Joins standardized Inventory data (Milestone 3 Phase 1) with the
latest persisted batch forecast (Milestone 3 Phase 2C) and turns the
result into per-product reorder recommendations, using ReorderService
for the numbers and StockRiskService for the risk classification.

Consumes ONLY the standardized representation and the forecast
engine's saved output - it never re-derives demand itself and never
reads uploaded files directly, so it stays independent of any
dataset's original schema.
=============================================================================
"""

from datetime import datetime

import pandas as pd

from config import (
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_OVERSTOCK_FACTOR,
    DEFAULT_REVIEW_PERIOD_DAYS,
    DEFAULT_SERVICE_LEVEL,
    EXPORTS_DIR
)

from services.standardization_service import StandardizationService
from services.forecast_service import ForecastService
from services.reorder_service import ReorderService
from services.stock_risk_service import StockRiskService

from utils.inventory_calculator import InventoryCalculator


class InventoryService:

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @staticmethod
    def generate_recommendations(
            dataset_id: int,
            lead_time_days: float | None = None,
            review_period_days: float | None = None,
            service_level: float | None = None,
            overstock_factor: float | None = None
    ) -> dict:
        """
        Build inventory recommendations for every product (and store,
        when the dataset's Inventory data carries one) in a dataset.

        Returns:

            {
                "recommendations": DataFrame (Output Structure),
                "notes": [str],
                "forecast_granularity": str,
                "forecast_horizon": int,
                "forecast_created_at": datetime,
                "generated_at": datetime
            }

        Raises ValueError when there is no standardized Inventory data
        or no saved batch forecast to build on - both are dataset-level
        preconditions, not per-row problems. Missing per-row data
        (a product with no forecast, a row with no current stock)
        never stops the run; it is reported as a note instead.
        """

        overstock_factor = overstock_factor or DEFAULT_OVERSTOCK_FACTOR

        inventory, products, notes = InventoryService._load_inventory(
            dataset_id
        )

        forecast = ForecastService.get_latest_batch_forecast(dataset_id)

        if forecast is None:

            raise ValueError(

                "No batch forecast found for this dataset. Run "

                "'Forecast All Products' on the Forecast page first."

            )

        demand_map = InventoryService._demand_map(forecast)

        price_map = InventoryService._price_map(products)

        name_map = InventoryService._name_map(products)

        rows = []

        missing_stock = 0

        no_forecast_products = set()

        generated_at = datetime.now()

        for _, item in inventory.iterrows():

            product_id = item.get("Product ID")

            if pd.isna(product_id):

                continue

            product_id = str(product_id)

            current_stock = item.get("Current Stock")

            if pd.isna(current_stock):

                missing_stock += 1

                continue

            current_stock = float(current_stock)

            demand = demand_map.get(product_id)

            if demand is None:

                no_forecast_products.add(product_id)

                forecast_total = 0.0

                forecast_periods = forecast.horizon

                daily_demand_std = None

            else:

                forecast_total = demand["total"]

                forecast_periods = demand["periods"]

                daily_demand_std = demand["daily_std"]

            row_lead_time = InventoryService._numeric_or(
                item.get("Lead Time"),
                lead_time_days
                if lead_time_days is not None
                else DEFAULT_LEAD_TIME_DAYS
            )

            row_safety_override = InventoryService._numeric_or(
                item.get("Safety Stock"),
                None
            )

            maximum_stock = InventoryService._numeric_or(
                item.get("Maximum Stock"),
                None
            )

            position = ReorderService.compute_position(

                current_stock,

                forecast_total,

                forecast_periods,

                forecast.granularity,

                lead_time_days=row_lead_time,

                review_period_days=(

                    review_period_days

                    if review_period_days is not None

                    else DEFAULT_REVIEW_PERIOD_DAYS

                ),

                service_level=(
                    service_level or DEFAULT_SERVICE_LEVEL
                ),

                daily_demand_std=daily_demand_std,

                safety_stock_override=row_safety_override,

                maximum_stock=maximum_stock

            )

            excess_units = InventoryCalculator.excess_units(

                position["available_inventory"],

                forecast_total,

                overstock_factor

            )

            classification = StockRiskService.classify(

                current_stock=current_stock,

                available_inventory=position["available_inventory"],

                reorder_point=position["reorder_point"],

                safety_stock=position["safety_stock"],

                forecast_demand=forecast_total,

                excess_units=excess_units,

                days_remaining=position["days_remaining"],

                lead_time_days=position["lead_time_days"]

            )

            unit_cost = price_map.get(product_id)

            rows.append({

                "Product ID": product_id,

                "Product Name": name_map.get(product_id, product_id),

                "Store ID": InventoryService._store_or_default(
                    item.get("Store ID")
                ),

                "Current Stock": current_stock,

                "Forecast Demand": round(forecast_total, 2),

                "Daily Avg Demand": round(
                    position["daily_avg_demand"], 2
                ),

                "Safety Stock": round(position["safety_stock"], 2),

                "Reorder Point": round(position["reorder_point"], 2),

                "Recommended Quantity": round(
                    position["recommended_quantity"], 2
                ),

                "Days Remaining": (

                    round(position["days_remaining"], 1)

                    if position["days_remaining"] is not None

                    else None

                ),

                "Lead Time (Days)": position["lead_time_days"],

                "Inventory Value": InventoryCalculator.inventory_value(
                    position["available_inventory"],
                    unit_cost
                ),

                "Risk Level": classification["risk_level"],

                "Status": classification["status"],

                "Reason": classification["reason"],

                "Recommendation Timestamp": generated_at

            })

        if missing_stock:

            notes.append(

                f"{missing_stock} inventory row(s) had no 'Current "

                f"Stock' value and were skipped."

            )

        if no_forecast_products:

            notes.append(

                f"{len(no_forecast_products)} product(s) in inventory "

                f"have no batch forecast (insufficient sales history "

                f"or new products); their recommendation is based on "

                f"current stock only."

            )

        forecasted_without_stock = (

            set(demand_map.keys())

            - set(inventory["Product ID"].dropna().astype(str))

        )

        if forecasted_without_stock:

            notes.append(

                f"{len(forecasted_without_stock)} forecasted product(s) "

                f"have no inventory record and were excluded from "

                f"recommendations."

            )

        recommendations = pd.DataFrame(rows)

        if not recommendations.empty:

            risk_order = {
                "Critical": 0,
                "High": 1,
                "Medium": 2,
                "Low": 3
            }

            recommendations["_risk_order"] = recommendations[
                "Risk Level"
            ].map(risk_order)

            recommendations = (

                recommendations

                .sort_values(
                    ["_risk_order", "Days Remaining"],
                    na_position="last"
                )

                .drop(columns=["_risk_order"])

                .reset_index(drop=True)

            )

        return {

            "recommendations": recommendations,

            "notes": notes,

            "forecast_granularity": forecast.granularity,

            "forecast_horizon": forecast.horizon,

            "forecast_created_at": forecast.created_at,

            "generated_at": generated_at

        }

    @staticmethod
    def export_csv(
            dataset_id: int,
            recommendations: pd.DataFrame
    ) -> str:
        """Save recommendations to EXPORTS_DIR and return the path."""

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        path = EXPORTS_DIR / (

            f"inventory_recommendations_dataset_{dataset_id}_"

            f"{datetime.now():%Y%m%d_%H%M%S}.csv"

        )

        recommendations.to_csv(path, index=False)

        return str(path)

    # -----------------------------------------------------------------
    # Internal steps
    # -----------------------------------------------------------------

    @staticmethod
    def _load_inventory(
            dataset_id: int
    ):
        """Standardized Inventory (required) and Products (optional)."""

        report = StandardizationService.load_with_report(dataset_id)

        notes = list(report["warnings"])

        frames = report["frames"]

        inventory = frames.get("Inventory")

        if inventory is None or inventory.empty:

            raise ValueError(

                "No standardized Inventory data available for this "

                "dataset. Upload an Inventory file with 'Product ID' "

                "and 'Current Stock' mapped."

            )

        if "Product ID" not in inventory.columns:

            raise ValueError(

                "Inventory data has no 'Product ID' mapped."

            )

        if "Current Stock" not in inventory.columns:

            raise ValueError(

                "Inventory data has no 'Current Stock' mapped."

            )

        products = frames.get("Products")

        return inventory, products, notes

    @staticmethod
    def _demand_map(
            forecast
    ) -> dict:
        """
        {product_id: {"total", "periods", "daily_std"}} built from a
        batch forecast's points.

        daily_std estimates day-to-day demand variability from each
        point's confidence band (~95% => width = 2 * 1.96 * std),
        letting safety stock reflect how volatile the forecast really
        is instead of a flat assumption.
        """

        by_product: dict[str, list] = {}

        for point in forecast.points:

            if point.product_id is None:

                continue

            by_product.setdefault(point.product_id, []).append(point)

        period_days = InventoryCalculator.period_days(
            forecast.granularity
        )

        demand_map = {}

        for product_id, points in by_product.items():

            total = sum(point.value for point in points)

            stds = [

                (point.upper - point.lower) / (2 * 1.96) / period_days

                for point in points

                if point.upper is not None and point.lower is not None

            ]

            daily_std = (

                sum(stds) / len(stds)

                if stds

                else None

            )

            demand_map[product_id] = {

                "total": float(total),

                "periods": len(points),

                "daily_std": daily_std

            }

        return demand_map

    @staticmethod
    def _price_map(
            products: pd.DataFrame | None
    ) -> dict:
        """{product_id: unit cost}, preferring Cost Price over Selling
        Price (inventory is normally valued at cost)."""

        if products is None or "Product ID" not in products.columns:

            return {}

        price_column = next(

            (

                column

                for column in ("Cost Price", "Selling Price")

                if column in products.columns

            ),

            None

        )

        if price_column is None:

            return {}

        priced = (

            products

            .dropna(subset=["Product ID"])

            .drop_duplicates(subset=["Product ID"])

        )

        return {

            str(row["Product ID"]): (

                float(row[price_column])

                if pd.notna(row[price_column])

                else None

            )

            for _, row in priced.iterrows()

        }

    @staticmethod
    def _name_map(
            products: pd.DataFrame | None
    ) -> dict:

        if (

                products is None

                or "Product ID" not in products.columns

                or "Product Name" not in products.columns

        ):

            return {}

        named = (

            products

            .dropna(subset=["Product ID"])

            .drop_duplicates(subset=["Product ID"])

        )

        return {

            str(row["Product ID"]): row["Product Name"]

            for _, row in named.iterrows()

        }

    @staticmethod
    def _store_or_default(
            value,
            default: str = "All Stores"
    ) -> str:
        """Blank/NaN Store ID reads as one pooled location."""

        if value is None:

            return default

        try:

            if pd.isna(value):

                return default

        except (TypeError, ValueError):

            pass

        text = str(value).strip()

        return text if text else default

    @staticmethod
    def _numeric_or(
            value,
            default
    ):
        """Coerce a possibly-missing dataframe cell to float, or
        fall back to `default` when it is NaN/None/unparsable."""

        if value is None:

            return default

        try:

            if pd.isna(value):

                return default

        except (TypeError, ValueError):

            pass

        try:

            return float(value)

        except (TypeError, ValueError):

            return default
