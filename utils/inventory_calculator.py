"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : inventory_calculator.py

Description :
Milestone 3 - Phase 3: the inventory formulas, and nothing else.

Every calculation is a separate pure function taking plain numbers, so
a formula can be changed (or replaced with a client-specific policy)
without touching the services that orchestrate them. No pandas, no
database, no Streamlit.
=============================================================================
"""

import math


class InventoryCalculator:

    # How many calendar days one forecast period covers.
    PERIOD_DAYS = {

        "Daily": 1.0,

        "Weekly": 7.0,

        "Monthly": 30.0

    }

    # -----------------------------------------------------------------
    # Horizon helpers
    # -----------------------------------------------------------------

    @staticmethod
    def period_days(
            granularity: str
    ) -> float:
        """Calendar days in one forecast period."""

        return InventoryCalculator.PERIOD_DAYS.get(granularity, 30.0)

    @staticmethod
    def horizon_days(
            periods: int,
            granularity: str
    ) -> float:
        """Calendar days covered by a forecast of `periods` periods."""

        return float(periods) * InventoryCalculator.period_days(
            granularity
        )

    # -----------------------------------------------------------------
    # Demand
    # -----------------------------------------------------------------

    @staticmethod
    def daily_average_demand(
            forecast_total: float,
            horizon_days: float
    ) -> float:
        """Forecast demand spread evenly over the forecast horizon."""

        if horizon_days <= 0:

            return 0.0

        return max(float(forecast_total), 0.0) / float(horizon_days)

    @staticmethod
    def demand_during_lead_time(
            daily_average_demand: float,
            lead_time_days: float
    ) -> float:
        """Demand expected to arise while a replenishment is in transit."""

        return max(daily_average_demand, 0.0) * max(
            float(lead_time_days),
            0.0
        )

    # -----------------------------------------------------------------
    # Buffers and trigger points
    # -----------------------------------------------------------------

    @staticmethod
    def safety_stock(
            daily_average_demand: float,
            lead_time_days: float,
            daily_demand_std: float | None = None,
            service_level_z: float = 1.65,
            minimum_days: float = 0.0
    ) -> float:
        """
        Buffer against demand variability during the lead time.

        Statistical formula (z * sigma * sqrt(lead time)) when the
        forecast tells us how volatile demand is; otherwise a simple
        days-of-cover buffer. The larger of the two is kept so a
        volatile product never ends up with less than the configured
        minimum cover.
        """

        lead_time_days = max(float(lead_time_days), 0.0)

        floor = max(daily_average_demand, 0.0) * max(
            float(minimum_days),
            0.0
        )

        if daily_demand_std is None or daily_demand_std <= 0:

            return floor

        statistical = (

            float(service_level_z)

            * float(daily_demand_std)

            * math.sqrt(lead_time_days)

        )

        return max(statistical, floor)

    @staticmethod
    def reorder_point(
            lead_time_demand: float,
            safety_stock: float
    ) -> float:
        """Stock level at which a replenishment order must be placed."""

        return max(lead_time_demand, 0.0) + max(safety_stock, 0.0)

    @staticmethod
    def target_stock_level(
            daily_average_demand: float,
            lead_time_days: float,
            review_period_days: float,
            safety_stock: float
    ) -> float:
        """
        Order-up-to level: cover demand until the next review AND the
        lead time that follows it, plus the safety buffer.
        """

        cover_days = max(float(lead_time_days), 0.0) + max(
            float(review_period_days),
            0.0
        )

        return (

            max(daily_average_demand, 0.0) * cover_days

            + max(safety_stock, 0.0)

        )

    # -----------------------------------------------------------------
    # Stock position
    # -----------------------------------------------------------------

    @staticmethod
    def available_inventory(
            current_stock: float,
            on_order: float = 0.0,
            reserved: float = 0.0
    ) -> float:
        """
        Stock that can actually serve future demand: what is on the
        shelf, plus what is already ordered, minus what is committed.
        """

        return (

            float(current_stock)

            + float(on_order)

            - float(reserved)

        )

    @staticmethod
    def days_of_inventory_remaining(
            available_inventory: float,
            daily_average_demand: float
    ) -> float | None:
        """
        Days until stock runs out. None means "no forecast demand", not
        zero days - the caller must not treat it as an imminent
        stock-out.
        """

        if daily_average_demand <= 0:

            return None

        return max(available_inventory, 0.0) / daily_average_demand

    # -----------------------------------------------------------------
    # Replenishment
    # -----------------------------------------------------------------

    @staticmethod
    def recommended_reorder_quantity(
            available_inventory: float,
            reorder_point: float,
            target_stock_level: float,
            minimum_order_quantity: float = 0.0,
            order_multiple: float = 1.0,
            maximum_stock: float | None = None
    ) -> float:
        """
        How much to order right now.

        Nothing is ordered while stock is above the reorder point.
        Below it, the gap up to the target level is ordered, raised to
        the supplier minimum, rounded up to the order multiple and
        capped so the maximum stock level is never exceeded.
        """

        if available_inventory > reorder_point:

            return 0.0

        quantity = max(target_stock_level - available_inventory, 0.0)

        if quantity <= 0:

            return 0.0

        quantity = max(quantity, float(minimum_order_quantity))

        if order_multiple and order_multiple > 0:

            quantity = (

                math.ceil(quantity / float(order_multiple))

                * float(order_multiple)

            )

        else:

            quantity = math.ceil(quantity)

        if maximum_stock is not None:

            headroom = float(maximum_stock) - available_inventory

            quantity = min(quantity, max(headroom, 0.0))

        return float(max(quantity, 0.0))

    # -----------------------------------------------------------------
    # Value and excess
    # -----------------------------------------------------------------

    @staticmethod
    def inventory_value(
            units: float,
            unit_cost: float | None
    ) -> float | None:
        """Monetary value of a stock position, None without a price."""

        if unit_cost is None:

            return None

        return max(float(units), 0.0) * float(unit_cost)

    @staticmethod
    def excess_units(
            available_inventory: float,
            forecast_demand: float,
            overstock_factor: float
    ) -> float:
        """
        Units held beyond the overstock threshold. Zero when demand is
        unknown (0), because "no forecast" is not evidence of excess.
        """

        if forecast_demand <= 0:

            return 0.0

        threshold = float(forecast_demand) * float(overstock_factor)

        return max(available_inventory - threshold, 0.0)
