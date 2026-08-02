"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/recommendation.py

Description :
Phase 8 - the public entry point the UI calls. Maps one row of
InventoryService's recommendations output to the "Input to AI" fields,
then runs it through prompt_builder -> ai_service -> formatter.

This is the only module in the ai/ package that knows the shape of
InventoryService's output columns - everything downstream of it works
with the generic "payload" dict, so a change to the inventory output
schema only ever touches this one mapping.
=============================================================================
"""

from ai.ai_service import AIService
from ai.formatter import format_response
from ai.prompt_builder import build_prompts


class AIRecommendationService:

    @staticmethod
    def build_payload(
            row: dict
    ) -> dict:
        """
        Maps one InventoryService recommendation row to the AI input
        fields from the handover spec (Product Name, Forecasted
        Demand, Current Inventory, Recommended Inventory, Reorder
        Quantity, Stock Status, Stock-out Risk, Demand Change %,
        Category, Season), plus a little extra real context (store,
        days remaining, whether current stock is actual or assumed)
        so the model can caveat correctly - never anything not
        already computed by the Forecast/Inventory layers.
        """

        return {

            "product_name": row.get("Product Name"),

            "category": row.get("Category"),

            "season": row.get("Season"),

            "store_id": row.get("Store ID"),

            "forecasted_demand": row.get("Forecast Demand"),

            "demand_change_pct": row.get("Demand Change %"),

            "current_inventory": row.get("Current Stock"),

            "stock_basis": row.get("Stock Basis"),

            "recommended_inventory": row.get("Target Stock Level"),

            "reorder_quantity": row.get("Recommended Quantity"),

            "days_remaining": row.get("Days Remaining"),

            "stock_status": row.get("Status"),

            "stockout_risk": row.get("Risk Level")

        }

    @staticmethod
    def generate(
            row: dict
    ) -> dict:
        """
        Full pipeline for one product: build the payload, build the
        prompts, call the model, parse the response.

        Returns the formatter's structured dict (see
        ai/formatter.py). Raises ValueError on any failure along the
        way - callers should catch it and surface the message as-is,
        it is already written for an end user.
        """

        payload = AIRecommendationService.build_payload(row)

        system_prompt, user_prompt = build_prompts(payload)

        raw_response = AIService.generate(system_prompt, user_prompt)

        return format_response(raw_response)
