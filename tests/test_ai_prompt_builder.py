"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_ai_prompt_builder.py

Description :
Unit tests for the Phase 8 AI layer's prompt construction
(ai/prompt_builder.py). Pure string-building - no API calls.

Run with either:
    python tests/test_ai_prompt_builder.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.config import NOT_AVAILABLE
from ai.prompt_builder import build_prompts, build_user_prompt


FULL_PAYLOAD = {

    "product_name": "Notebook",

    "category": "Stationery",

    "season": "All Season",

    "store_id": "S1",

    "forecasted_demand": 329.6,

    "demand_change_pct": -0.7,

    "current_inventory": 194.57,

    "stock_basis": "Actual",

    "recommended_inventory": 194.57,

    "reorder_quantity": 0,

    "days_remaining": 17.7,

    "stock_status": "Adequate",

    "stockout_risk": "Low"

}


def test_build_user_prompt_includes_every_field():

    prompt = build_user_prompt(FULL_PAYLOAD)

    assert "Notebook" in prompt

    assert "Stationery" in prompt

    assert "S1" in prompt

    assert "-0.7%" in prompt

    assert "Adequate" in prompt

    assert "Low" in prompt


def test_build_user_prompt_marks_missing_fields_not_available():

    payload = dict(FULL_PAYLOAD)

    payload["category"] = None

    payload["season"] = None

    prompt = build_user_prompt(payload)

    assert prompt.count(NOT_AVAILABLE) == 2


def test_build_user_prompt_never_invents_a_value_for_missing_data():

    payload = {key: None for key in FULL_PAYLOAD}

    prompt = build_user_prompt(payload)

    # Every field renders as explicitly missing, not blank/omitted/0.
    assert prompt.count(NOT_AVAILABLE) == len(FULL_PAYLOAD)


def test_build_prompts_returns_system_and_user():

    system_prompt, user_prompt = build_prompts(FULL_PAYLOAD)

    assert "JSON" in system_prompt

    assert "250 words" in system_prompt

    assert "Notebook" in user_prompt


def test_system_prompt_names_all_five_sections():

    system_prompt, _ = build_prompts(FULL_PAYLOAD)

    for key in (

            "executive_summary",

            "business_recommendation",

            "inventory_action",

            "risk_explanation",

            "final_recommendation"

    ):

        assert key in system_prompt


# ---------------------------------------------------------------------
# Plain-python runner
# ---------------------------------------------------------------------

if __name__ == "__main__":

    failures = 0

    tests = [

        (name, function)

        for name, function in sorted(globals().items())

        if name.startswith("test_") and callable(function)

    ]

    for name, function in tests:

        try:

            function()

            print(f"PASS  {name}")

        except Exception as error:

            failures += 1

            print(f"FAIL  {name}: {error}")

    print(

        f"\n{len(tests) - failures}/{len(tests)} tests passed."

    )

    sys.exit(1 if failures else 0)
