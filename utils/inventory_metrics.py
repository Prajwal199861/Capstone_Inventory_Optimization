"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : inventory_metrics.py

Description :
Milestone 3 - Phase 3: aggregate KPIs over a set of inventory
recommendations (the Output Structure produced by InventoryService).

Kept separate from InventoryCalculator (which computes ONE product's
numbers) so summarizing many recommendations for dashboards/reports
can change independently of the per-row formulas.
=============================================================================
"""

import pandas as pd


class InventoryMetrics:

    REORDER_STATUSES = {"Reorder Required"}

    STOCKOUT_RISK_LEVELS = {"Critical", "High"}

    @staticmethod
    def summarize(
            recommendations: pd.DataFrame
    ) -> dict:
        """
        Dashboard KPI row for a recommendations table.

        Returns:

            {
                "products_to_reorder": int,
                "critical_stockouts": int,
                "overstocked_products": int,
                "inventory_value": float | None,
                "avg_days_remaining": float | None,
                "total_products": int
            }

        Safe on an empty/missing-column DataFrame - every KPI falls
        back to 0/None rather than raising.
        """

        if recommendations is None or recommendations.empty:

            return {

                "products_to_reorder": 0,

                "critical_stockouts": 0,

                "overstocked_products": 0,

                "inventory_value": None,

                "avg_days_remaining": None,

                "total_products": 0

            }

        products_to_reorder = int(

            recommendations.get(
                "Status",
                pd.Series(dtype=object)
            ).isin(InventoryMetrics.REORDER_STATUSES).sum()

        )

        critical_stockouts = int(

            recommendations.get(
                "Risk Level",
                pd.Series(dtype=object)
            ).eq("Critical").sum()

        )

        overstocked_products = int(

            recommendations.get(
                "Status",
                pd.Series(dtype=object)
            ).eq("Overstock Warning").sum()

        )

        inventory_value = None

        if "Inventory Value" in recommendations.columns:

            values = recommendations["Inventory Value"].dropna()

            if not values.empty:

                inventory_value = float(values.sum())

        avg_days_remaining = None

        if "Days Remaining" in recommendations.columns:

            days = pd.to_numeric(

                recommendations["Days Remaining"],

                errors="coerce"

            ).dropna()

            if not days.empty:

                avg_days_remaining = float(days.mean())

        return {

            "products_to_reorder": products_to_reorder,

            "critical_stockouts": critical_stockouts,

            "overstocked_products": overstocked_products,

            "inventory_value": inventory_value,

            "avg_days_remaining": avg_days_remaining,

            "total_products": int(len(recommendations))

        }

    @staticmethod
    def risk_breakdown(
            recommendations: pd.DataFrame
    ) -> dict:
        """{risk_level: count}, always including every known level."""

        levels = ["Critical", "High", "Medium", "Low"]

        if (

                recommendations is None

                or recommendations.empty

                or "Risk Level" not in recommendations.columns

        ):

            return {level: 0 for level in levels}

        counts = (

            recommendations["Risk Level"]

            .value_counts()

            .to_dict()

        )

        return {level: int(counts.get(level, 0)) for level in levels}
