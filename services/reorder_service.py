"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : reorder_service.py

Description :
Milestone 3 - Phase 3: computes one product's full stock position
(demand rates, safety stock, reorder point, target level, recommended
reorder quantity) by running the InventoryCalculator formulas in the
right order.

Kept as its own module - separate from InventoryService (which loads
and joins data) and StockRiskService (which turns the position into a
Risk Level/Status) - so the replenishment math can be swapped out
independently, per the handover's "keep each calculation isolated"
guidance.
=============================================================================
"""

from config import (
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_MINIMUM_ORDER_QUANTITY,
    DEFAULT_ORDER_MULTIPLE,
    DEFAULT_REVIEW_PERIOD_DAYS,
    DEFAULT_SAFETY_STOCK_DAYS,
    DEFAULT_SERVICE_LEVEL,
    SERVICE_LEVEL_Z_SCORES
)

from utils.inventory_calculator import InventoryCalculator


class ReorderService:

    @staticmethod
    def service_level_z(
            service_level: float
    ) -> float:
        """Nearest configured z-score, defaulting to the 95% level."""

        if service_level in SERVICE_LEVEL_Z_SCORES:

            return SERVICE_LEVEL_Z_SCORES[service_level]

        return SERVICE_LEVEL_Z_SCORES[DEFAULT_SERVICE_LEVEL]

    @staticmethod
    def compute_position(
            current_stock: float | None,
            forecast_total: float,
            forecast_periods: int,
            granularity: str,
            lead_time_days: float | None = None,
            review_period_days: float | None = None,
            service_level: float | None = None,
            daily_demand_std: float | None = None,
            safety_stock_override: float | None = None,
            minimum_order_quantity: float = DEFAULT_MINIMUM_ORDER_QUANTITY,
            order_multiple: float = DEFAULT_ORDER_MULTIPLE,
            maximum_stock: float | None = None,
            on_order: float = 0.0,
            reserved: float = 0.0
    ) -> dict:
        """
        Full stock position for one product (optionally, one
        product-store row).

        current_stock=None means the dataset has no actual reading for
        this product: stock is assumed to have started at 0 and since
        settled at a healthy operating level - the target (order-up-to)
        stock level the formulas already compute from demand/lead time/
        review period - rather than blocking the recommendation
        entirely or defaulting to the safety-stock floor, which sits
        right at the reorder trigger and would misreport a merely
        unknown stock level as urgent. Real data always wins when it
        is present - this path only ever runs when it truly is not.

        Returns:

            {
                "current_stock", "stock_assumed", "daily_avg_demand",
                "lead_time_demand", "safety_stock", "reorder_point",
                "target_stock_level", "available_inventory",
                "days_remaining", "recommended_quantity"
            }
        """

        lead_time_days = (

            lead_time_days

            if lead_time_days is not None

            else DEFAULT_LEAD_TIME_DAYS

        )

        review_period_days = (

            review_period_days

            if review_period_days is not None

            else DEFAULT_REVIEW_PERIOD_DAYS

        )

        service_level = service_level or DEFAULT_SERVICE_LEVEL

        horizon_days = InventoryCalculator.horizon_days(

            forecast_periods,

            granularity

        )

        daily_avg_demand = InventoryCalculator.daily_average_demand(

            forecast_total,

            horizon_days

        )

        lead_time_demand = InventoryCalculator.demand_during_lead_time(

            daily_avg_demand,

            lead_time_days

        )

        if safety_stock_override is not None:

            safety_stock = max(float(safety_stock_override), 0.0)

        else:

            safety_stock = InventoryCalculator.safety_stock(

                daily_avg_demand,

                lead_time_days,

                daily_demand_std=daily_demand_std,

                service_level_z=ReorderService.service_level_z(
                    service_level
                ),

                minimum_days=DEFAULT_SAFETY_STOCK_DAYS

            )

        reorder_point = InventoryCalculator.reorder_point(

            lead_time_demand,

            safety_stock

        )

        target_stock_level = InventoryCalculator.target_stock_level(

            daily_avg_demand,

            lead_time_days,

            review_period_days,

            safety_stock

        )

        stock_assumed = current_stock is None

        if stock_assumed:

            current_stock = target_stock_level

        available_inventory = InventoryCalculator.available_inventory(

            current_stock,

            on_order=on_order,

            reserved=reserved

        )

        days_remaining = InventoryCalculator.days_of_inventory_remaining(

            available_inventory,

            daily_avg_demand

        )

        recommended_quantity = (

            InventoryCalculator.recommended_reorder_quantity(

                available_inventory,

                reorder_point,

                target_stock_level,

                minimum_order_quantity=minimum_order_quantity,

                order_multiple=order_multiple,

                maximum_stock=maximum_stock

            )

        )

        return {

            "current_stock": current_stock,

            "stock_assumed": stock_assumed,

            "daily_avg_demand": daily_avg_demand,

            "lead_time_demand": lead_time_demand,

            "safety_stock": safety_stock,

            "reorder_point": reorder_point,

            "target_stock_level": target_stock_level,

            "available_inventory": available_inventory,

            "days_remaining": days_remaining,

            "recommended_quantity": recommended_quantity,

            "lead_time_days": lead_time_days

        }
