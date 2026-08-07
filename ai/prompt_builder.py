"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/prompt_builder.py

Description :
Phase 8 - builds the system and user prompts sent to the model. Pure
string building only - no API calls, no database. Kept separate from
ai_service.py so the prompt wording can change without touching how
the model is called, per the same "isolate calculations" principle
used across the app's other services.
=============================================================================
"""

from ai.config import NOT_AVAILABLE
from ai.utils import format_value


SYSTEM_PROMPT = f"""You are a retail inventory decision-support assistant.
You interpret structured forecasting and inventory data into clear,
professional business insights for a retail operations audience.

Rules you must follow:
- Use ONLY the data given to you in the user message. Never invent
  numbers, trends, causes, or facts that are not present in the input.
- If a field is marked "{NOT_AVAILABLE}", say so plainly rather than
  guessing a value or ignoring the gap.
- If current-inventory figures are marked as assumed rather than
  actual, mention that the recommendation relies on an assumption.
- Write in plain, professional business language - no jargon, no
  emojis, no markdown formatting inside the text values.
- Keep the combined response under 250 words in total.
- Respond with ONLY a single JSON object, no other text before or
  after it, matching exactly this schema (all values are strings):

{{
  "executive_summary": "...",
  "business_recommendation": "...",
  "inventory_action": "...",
  "risk_explanation": "...",
  "final_recommendation": "..."
}}
"""


_FIELD_LABELS = [

    ("product_name", "Product"),

    ("category", "Category"),

    ("season", "Season"),

    ("store_id", "Store"),

    ("forecasted_demand", "Forecasted Demand (upcoming horizon)"),

    ("demand_change_pct", "Demand Change vs. recent history", "%"),

    ("current_inventory", "Current Inventory"),

    ("stock_basis", "Current Inventory Basis"),

    ("recommended_inventory", "Recommended Inventory Level"),

    ("reorder_quantity", "Reorder Quantity"),

    ("days_remaining", "Estimated Days of Stock Remaining"),

    ("stock_status", "Stock Status"),

    ("stockout_risk", "Stock-out Risk Level")

]


def build_user_prompt(
        payload: dict
) -> str:
    """Renders the payload as a labeled data block plus the final
    instruction, from the exact "Input to AI" fields the handover doc
    specifies (plus a little extra real context - store, days
    remaining, stock basis - never anything fabricated)."""

    lines = ["Product data:"]

    for entry in _FIELD_LABELS:

        key, label = entry[0], entry[1]

        suffix = entry[2] if len(entry) > 2 else ""

        lines.append(
            f"- {label}: {format_value(payload.get(key), suffix)}"
        )

    lines.append(
        "\nGenerate the JSON response now, following the rules above."
    )

    return "\n".join(lines)


def build_prompts(
        payload: dict
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for one product."""

    return SYSTEM_PROMPT, build_user_prompt(payload)


# -----------------------------------------------------------------
# Milestone 4 - Phase 3: AI Executive Report (dataset-wide, not
# per-product). Same rules as the per-product prompt - use only
# supplied data, never invent numbers - just a different JSON
# contract (see ai/config.py EXECUTIVE_SECTIONS).
# -----------------------------------------------------------------

EXECUTIVE_SYSTEM_PROMPT = """You are a retail operations analyst \
producing an executive summary for store/inventory managers from \
already-computed forecasting and inventory-optimization results for \
one dataset.

Rules you must follow:
- Use ONLY the data given to you in the user message. Never invent
  numbers, product names, trends or facts that are not present in
  the input.
- If a field is marked "Not available", say so plainly rather than
  guessing a value or ignoring the gap.
- Write in plain, professional business language for a retail
  operations manager - no jargon, no emojis, no markdown formatting
  inside the text values.
- Keep the combined response under 400 words in total.
- Respond with ONLY a single JSON object, no other text before or
  after it, matching exactly this schema (all values are strings):

{
  "overall_health": "...",
  "critical_issues": "...",
  "positive_findings": "...",
  "immediate_actions": "...",
  "management_recommendations": "..."
}
"""

_EXECUTIVE_FIELD_LABELS = [

    ("dataset_name", "Dataset"),

    ("total_products", "Total Products"),

    ("forecast_model", "Forecast Model"),

    ("forecast_granularity", "Forecast Granularity"),

    ("forecast_horizon", "Forecast Horizon (periods)"),

    ("critical_count", "Products at Critical Risk"),

    ("high_count", "Products at High Risk"),

    ("medium_count", "Products at Medium Risk"),

    ("low_count", "Products at Low Risk"),

    ("reorder_count", "Products Needing Reorder"),

    ("overstock_count", "Overstocked Products"),

    ("total_inventory_value", "Total Inventory Value", "$"),

    ("avg_days_remaining", "Average Days of Stock Remaining")

]


def _format_product_list(
        products: list
) -> str:

    if not products:

        return "  None"

    return "\n".join(

        f"  - {item.get('name', 'Unknown')} "
        f"({item.get('detail', 'no further detail')})"

        for item in products

    )


def build_executive_user_prompt(
        payload: dict
) -> str:
    """Renders the dataset-wide aggregate payload (see
    ReportService.ai_executive_payload) as a labeled data block, the
    same "use only what's here" contract as the per-product prompt."""

    lines = ["Dataset-wide inventory & forecast summary:"]

    for entry in _EXECUTIVE_FIELD_LABELS:

        key, label = entry[0], entry[1]

        suffix = entry[2] if len(entry) > 2 else ""

        lines.append(
            f"- {label}: {format_value(payload.get(key), suffix)}"
        )

    lines.append("\nTop Critical-Risk Products:")

    lines.append(
        _format_product_list(payload.get("top_critical_products", []))
    )

    lines.append("\nTop Overstocked Products:")

    lines.append(
        _format_product_list(
            payload.get("top_overstocked_products", [])
        )
    )

    lines.append(
        "\nGenerate the JSON response now, following the rules above."
    )

    return "\n".join(lines)


def build_executive_prompts(
        payload: dict
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for the dataset-wide AI
    Executive Report."""

    return EXECUTIVE_SYSTEM_PROMPT, build_executive_user_prompt(payload)
