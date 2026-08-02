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
from services.demand_service import DemandService
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

        Raises ValueError only when there is no saved batch forecast to
        build on - that is the one true dataset-level precondition
        (there is no demand to optimize against without it). Missing
        Inventory data is NOT a precondition: when a product has no
        current-stock reading (no Inventory file at all, a missing
        'Current Stock' column, or a blank cell for that row), stock is
        assumed to have started at 0 and settled at a healthy
        operating (target order-up-to) level rather than blocking the
        recommendation - real data always wins when it is present.
        Every assumed row is flagged via the "Stock Basis" column and
        a summary note.
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

        category_map = InventoryService._column_map(products, "Category")

        season_map = InventoryService._column_map(products, "Season")

        historical_map, history_notes = (
            InventoryService._historical_demand_map(dataset_id, forecast)
        )

        notes.extend(history_notes)

        rows = []

        assumed_stock_count = 0

        no_forecast_products = set()

        generated_at = datetime.now()

        for item in InventoryService._iter_inventory_rows(
                inventory,
                demand_map
        ):

            product_id = item["product_id"]

            current_stock = item["current_stock"]

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

            historical_total = historical_map.get(product_id)

            demand_change_pct = (

                round(

                    (
                        (forecast_total - historical_total)
                        / historical_total
                    ) * 100,

                    1

                )

                if historical_total

                else None

            )

            row_lead_time = InventoryService._numeric_or(
                item.get("lead_time"),
                lead_time_days
                if lead_time_days is not None
                else DEFAULT_LEAD_TIME_DAYS
            )

            row_safety_override = InventoryService._numeric_or(
                item.get("safety_stock_override"),
                None
            )

            maximum_stock = InventoryService._numeric_or(
                item.get("maximum_stock"),
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

                current_stock=position["current_stock"],

                available_inventory=position["available_inventory"],

                reorder_point=position["reorder_point"],

                safety_stock=position["safety_stock"],

                forecast_demand=forecast_total,

                excess_units=excess_units,

                days_remaining=position["days_remaining"],

                lead_time_days=position["lead_time_days"],

                stock_assumed=position["stock_assumed"]

            )

            reason = classification["reason"]

            if position["stock_assumed"]:

                assumed_stock_count += 1

                reason = (

                    "No current-stock data was provided for this "

                    "product; stock is assumed to have started at 0 "

                    "and settled at a healthy operating (target) "

                    "level. " + reason

                )

            unit_cost = price_map.get(product_id)

            rows.append({

                "Product ID": product_id,

                "Product Name": name_map.get(product_id, product_id),

                "Category": category_map.get(product_id),

                "Season": season_map.get(product_id),

                "Store ID": item["store_id"],

                "Current Stock": round(position["current_stock"], 2),

                "Stock Basis": (
                    "Assumed"
                    if position["stock_assumed"]
                    else "Actual"
                ),

                "Forecast Demand": round(forecast_total, 2),

                "Demand Change %": demand_change_pct,

                "Target Stock Level": round(
                    position["target_stock_level"], 2
                ),

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

                "Reason": reason,

                "Recommendation Timestamp": generated_at

            })

        if assumed_stock_count:

            notes.append(

                f"{assumed_stock_count} product(s) had no current-stock "

                f"data; their recommendation assumes stock started at "

                f"0 and has since settled at a healthy operating "

                f"(target) level. Upload/map an Inventory file with "

                f"'Current Stock' for accurate numbers."

            )

        if no_forecast_products:

            notes.append(

                f"{len(no_forecast_products)} product(s) in inventory "

                f"have no batch forecast (insufficient sales history "

                f"or new products); their recommendation is based on "

                f"current stock only."

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
        """
        Standardized Inventory (optional - see class docstring on
        generate_recommendations for the fallback when it is absent
        or has no 'Current Stock') and Products (optional, for names
        and unit cost).
        """

        report = StandardizationService.load_with_report(dataset_id)

        notes = list(report["warnings"])

        frames = report["frames"]

        inventory = frames.get("Inventory")

        if inventory is None or inventory.empty:

            notes.append(

                "No standardized Inventory data available for this "

                "dataset; current stock will be assumed to have "

                "started at 0 and settled at a healthy operating "

                "level for every forecasted product."

            )

            inventory = None

        elif "Product ID" not in inventory.columns:

            raise ValueError(

                "Inventory data has no 'Product ID' mapped."

            )

        elif "Current Stock" not in inventory.columns:

            notes.append(

                "Inventory data has no 'Current Stock' mapped; "

                "current stock will be assumed to have started at 0 "

                "and settled at a healthy operating level for every "

                "product."

            )

        products = frames.get("Products")

        return inventory, products, notes

    @staticmethod
    def _iter_inventory_rows(
            inventory: pd.DataFrame | None,
            demand_map: dict
    ) -> list:
        """
        Unifies real Inventory rows with synthetic rows for products
        that only exist in the forecast (no Inventory data for them at
        all), so both flow through one code path: real 'current_stock'
        when a value exists, None when it does not (whole entity
        missing, no 'Current Stock' column, or a blank cell) -
        ReorderService.compute_position() turns None into the assumed
        healthy-target-level fallback.

        Returns a list of dicts: {product_id, current_stock, store_id,
        lead_time, safety_stock_override, maximum_stock}.
        """

        rows = []

        covered_products = set()

        if inventory is not None:

            has_stock_column = "Current Stock" in inventory.columns

            for _, item in inventory.iterrows():

                product_id = item.get("Product ID")

                if pd.isna(product_id):

                    continue

                product_id = str(product_id)

                covered_products.add(product_id)

                raw_stock = (
                    item.get("Current Stock")
                    if has_stock_column
                    else None
                )

                current_stock = (

                    float(raw_stock)

                    if raw_stock is not None and pd.notna(raw_stock)

                    else None

                )

                rows.append({

                    "product_id": product_id,

                    "current_stock": current_stock,

                    "store_id": InventoryService._store_or_default(
                        item.get("Store ID")
                    ),

                    "lead_time": item.get("Lead Time"),

                    "safety_stock_override": item.get("Safety Stock"),

                    "maximum_stock": item.get("Maximum Stock")

                })

        for product_id in sorted(
                set(demand_map.keys()) - covered_products
        ):

            rows.append({

                "product_id": product_id,

                "current_stock": None,

                "store_id": "All Stores",

                "lead_time": None,

                "safety_stock_override": None,

                "maximum_stock": None

            })

        return rows

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
    def _column_map(
            products: pd.DataFrame | None,
            column: str
    ) -> dict:
        """{product_id: value} for any optional Products column (e.g.
        Category, Season). Empty when the dataset doesn't carry it -
        callers must treat a missing key as "not available", never
        guess a value."""

        if (

                products is None

                or "Product ID" not in products.columns

                or column not in products.columns

        ):

            return {}

        mapped = (

            products

            .dropna(subset=["Product ID"])

            .drop_duplicates(subset=["Product ID"])

        )

        return {

            str(row["Product ID"]): row[column]

            for _, row in mapped.iterrows()

            if pd.notna(row[column])

        }

    @staticmethod
    def _historical_demand_map(
            dataset_id: int,
            forecast
    ):
        """
        {product_id: trailing actual demand over the same number of
        periods as the forecast horizon}, the real computed baseline
        "Demand Change %" is measured against. A genuine calculation
        from historical sales - never something the AI layer is asked
        to estimate.

        Returns ({}, [note]) instead of raising when history can't be
        rebuilt for any reason - Demand Change % is supplementary
        context, never a precondition for recommendations.
        """

        try:

            product_data = DemandService.build_product_series_map(

                dataset_id,

                granularity=forecast.granularity,

                measure=forecast.measure

            )

        except ValueError as error:

            return {}, [

                f"Demand Change % is unavailable: {error}"

            ]

        return {

            product_id: float(series.tail(forecast.horizon).sum())

            for product_id, series in (
                product_data["series_map"].items()
            )

        }, []

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
