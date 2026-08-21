"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : inventory_simulation.py

Description :
Hotfix Phase 1: when a product has no actual "Current Stock" reading,
InventoryService previously assumed stock sat exactly at the target
(order-up-to) level. Because that level is driven by demand
*volatility* (safety stock) rather than demand *rate*, dividing it by
a near-zero forecast for a slow-moving product produced "Days
Remaining" in the millions.

This module estimates a believable current stock instead, by
replaying the product's historical demand against a simple
reorder-point / order-up-to policy: start from a sensible opening
balance, subtract each historical period's demand, and replenish back
to the target level whenever stock falls to or below the reorder
point. The stock left after the last historical period becomes the
estimate.

Pure logic - no database, no pandas indexing beyond a plain numpy
array, no Streamlit - so it is unit-testable and stays independent of
InventoryService (which decides WHEN to call it) and InventoryCalculator
/ ReorderService (whose formulas it reuses unchanged, never re-derives).
=============================================================================
"""

import pandas as pd

from config import MIN_SIMULATION_HISTORY_PERIODS


class InventorySimulationService:

    @staticmethod
    def simulate_current_stock(
            history: pd.Series | None,
            opening_stock: float,
            reorder_point: float,
            target_stock_level: float
    ) -> float | None:
        """
        Replays `history` (one demand value per period, oldest first -
        as produced by DemandService.build_product_series_map) against
        an opening balance:

            stock -= period demand           (floored at 0 - a store
                                               cannot sell stock it
                                               does not have)
            if stock <= reorder_point:
                stock += (target_stock_level - reorder_point)

        The replenishment quantity is fixed per cycle (the gap between
        the reorder trigger and the order-up-to level), mirroring a
        standard (s, S) reorder policy without needing to re-run the
        full ReorderService formulas on every period.

        Returns the stock remaining after the last historical period,
        or None when there is not enough history to simulate a
        believable trajectory - the caller falls back to the prior
        assumed-stock behaviour in that case.
        """

        if (
                history is None
                or len(history) < MIN_SIMULATION_HISTORY_PERIODS
        ):

            return None

        reorder_quantity = max(
            float(target_stock_level) - float(reorder_point),
            0.0
        )

        stock = max(float(opening_stock), 0.0)

        for demand in history.to_numpy(dtype=float):

            stock = max(stock - max(float(demand), 0.0), 0.0)

            if stock <= reorder_point and reorder_quantity > 0:

                stock += reorder_quantity

        return float(stock)
