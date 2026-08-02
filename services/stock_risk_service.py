"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : stock_risk_service.py

Description :
Milestone 3 - Phase 3: business rules that turn a product's computed
stock position into an action (Status) and a severity (Risk Level),
each with a human-readable reason.

Pure logic - no database, no pandas. Kept separate from the numeric
formulas (InventoryCalculator) so a rule can be tuned without
touching how the numbers themselves are computed.
=============================================================================
"""


class StockRiskService:

    RISK_LEVELS = ["Critical", "High", "Medium", "Low"]

    STATUS_REORDER_REQUIRED = "Reorder Required"

    STATUS_OVERSTOCK_WARNING = "Overstock Warning"

    STATUS_ADEQUATE = "Adequate"

    @staticmethod
    def classify(
            current_stock: float,
            available_inventory: float,
            reorder_point: float,
            safety_stock: float,
            forecast_demand: float,
            excess_units: float,
            days_remaining: float | None,
            lead_time_days: float,
            stock_assumed: bool = False
    ) -> dict:
        """
        Applies the Phase 3 business rules in priority order:

        1. Current Stock <= 0                    -> Critical, out of stock.
        2. Current Stock <= Reorder Point         -> Reorder Required, with
           severity escalated to High/Critical when stock is also below
           safety stock or will run out before a fresh order can arrive.
        3. Current Stock >> Forecast Demand       -> Overstock Warning.
        4. Otherwise                              -> Adequate / Low risk.

        stock_assumed=True means current_stock/available_inventory are
        not an actual reading (no inventory data was provided for this
        product) - rule 1 is skipped in that case, since claiming "0
        units on hand" would misrepresent an assumption as a fact.

        Returns {"risk_level", "status", "reason"}.
        """

        if not stock_assumed and current_stock <= 0:

            return {

                "risk_level": "Critical",

                "status": StockRiskService.STATUS_REORDER_REQUIRED,

                "reason": (

                    "Product is out of stock (0 units on hand); "

                    "reorder immediately."

                )

            }

        if available_inventory <= reorder_point:

            if available_inventory < safety_stock:

                return {

                    "risk_level": "High",

                    "status": StockRiskService.STATUS_REORDER_REQUIRED,

                    "reason": (

                        f"Stock ({available_inventory:,.0f} units) is "

                        f"below safety stock "

                        f"({safety_stock:,.0f} units); high risk of "

                        f"stock-out before replenishment arrives."

                    )

                }

            if (

                    days_remaining is not None

                    and days_remaining <= lead_time_days

            ):

                return {

                    "risk_level": "Critical",

                    "status": StockRiskService.STATUS_REORDER_REQUIRED,

                    "reason": (

                        f"Only {days_remaining:.1f} day(s) of stock "

                        f"remain, less than the "

                        f"{lead_time_days:.0f}-day lead time; a "

                        f"stock-out is expected before a new order "

                        f"can arrive."

                    )

                }

            return {

                "risk_level": "Medium",

                "status": StockRiskService.STATUS_REORDER_REQUIRED,

                "reason": (

                    f"Stock ({available_inventory:,.0f} units) is at "

                    f"or below the reorder point "

                    f"({reorder_point:,.0f} units); reorder now to "

                    f"avoid a stock-out."

                )

            }

        if excess_units > 0:

            return {

                "risk_level": "Low",

                "status": StockRiskService.STATUS_OVERSTOCK_WARNING,

                "reason": (

                    f"Stock ({available_inventory:,.0f} units) far "

                    f"exceeds forecast demand "

                    f"({forecast_demand:,.0f} units); "

                    f"{excess_units:,.0f} unit(s) are excess. "

                    f"Consider reducing future orders or running a "

                    f"promotion."

                )

            }

        if forecast_demand <= 0:

            return {

                "risk_level": "Low",

                "status": StockRiskService.STATUS_ADEQUATE,

                "reason": (

                    "No forecast demand is available for this "

                    "product; recommendation is based on current "

                    "stock only."

                )

            }

        return {

            "risk_level": "Low",

            "status": StockRiskService.STATUS_ADEQUATE,

            "reason": (

                "Stock is within the healthy range between the "

                "reorder point and the overstock threshold."

            )

        }
