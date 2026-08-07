"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_ai_executive_summary.py

Description :
Unit tests for the Milestone 4 - Phase 3 AI Executive Report path:
the new executive prompt (ai/prompt_builder.py), the generalized
formatter contract (ai/formatter.py), and
AIRecommendationService.generate_executive_summary() (ai/
recommendation.py). No live API calls - the missing-key path is
exercised the same way test_ai_recommendation.py does for the
per-product insight.

Run with either:
    python tests/test_ai_executive_summary.py
    python -m pytest tests/
=============================================================================
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.config import EXECUTIVE_SECTION_LABELS, EXECUTIVE_SECTIONS
from ai.formatter import format_response
from ai.prompt_builder import build_executive_prompts, build_executive_user_prompt

import ai.ai_service as ai_service_module
from ai.ai_service import AIService
from ai.recommendation import AIRecommendationService


SAMPLE_PAYLOAD = {

    "dataset_name": "Demo Dataset",

    "total_products": 25,

    "forecast_model": "Auto (per product)",

    "forecast_granularity": "Monthly",

    "forecast_horizon": 3,

    "critical_count": 4,

    "high_count": 6,

    "medium_count": 10,

    "low_count": 5,

    "reorder_count": 10,

    "overstock_count": 3,

    "total_inventory_value": 125000.0,

    "avg_days_remaining": 18.5,

    "top_critical_products": [

        {"name": "Widget", "detail": "Store 1 critical"}

    ],

    "top_overstocked_products": [

        {"name": "Gadget", "detail": "Way overstocked"}

    ]

}


SAMPLE_RESPONSE = {

    key: f"Text for {key}."

    for key in EXECUTIVE_SECTIONS

}


# ---------------------------------------------------------------------
# prompt_builder
# ---------------------------------------------------------------------

def test_build_executive_user_prompt_includes_dataset_name():

    prompt = build_executive_user_prompt(SAMPLE_PAYLOAD)

    assert "Demo Dataset" in prompt


def test_build_executive_user_prompt_includes_critical_products():

    prompt = build_executive_user_prompt(SAMPLE_PAYLOAD)

    assert "Widget" in prompt

    assert "Store 1 critical" in prompt


def test_build_executive_user_prompt_handles_no_critical_products():

    payload = dict(SAMPLE_PAYLOAD)

    payload["top_critical_products"] = []

    prompt = build_executive_user_prompt(payload)

    assert "None" in prompt


def test_build_executive_user_prompt_marks_missing_fields_not_available():

    prompt = build_executive_user_prompt({})

    assert "Not available" in prompt


def test_build_executive_prompts_returns_system_and_user():

    system, user = build_executive_prompts(SAMPLE_PAYLOAD)

    assert "JSON" in system

    assert "Demo Dataset" in user


def test_executive_system_prompt_names_all_five_sections():

    system, _ = build_executive_prompts(SAMPLE_PAYLOAD)

    for key in EXECUTIVE_SECTIONS:

        assert key in system


# ---------------------------------------------------------------------
# formatter (generalized contract)
# ---------------------------------------------------------------------

def test_format_response_accepts_executive_sections():

    result = format_response(

        json.dumps(SAMPLE_RESPONSE),

        sections=EXECUTIVE_SECTIONS,

        section_labels=EXECUTIVE_SECTION_LABELS,

        max_words=400

    )

    for key in EXECUTIVE_SECTIONS:

        assert result[key] == f"Text for {key}."

    assert result["missing_sections"] == []


def test_format_response_reports_missing_executive_sections():

    partial = {"overall_health": "All good."}

    result = format_response(

        json.dumps(partial),

        sections=EXECUTIVE_SECTIONS,

        section_labels=EXECUTIVE_SECTION_LABELS,

        max_words=400

    )

    assert result["overall_health"] == "All good."

    assert result["critical_issues"] == ""

    assert "Critical Issues" in result["missing_sections"]


def test_format_response_default_args_still_use_insight_sections():

    # Backward-compat: the per-product call site doesn't pass
    # sections/section_labels/max_words explicitly.
    per_product_response = {

        "executive_summary": "Summary.",

        "business_recommendation": "Recommendation.",

        "inventory_action": "Action.",

        "risk_explanation": "Explanation.",

        "final_recommendation": "Final."

    }

    result = format_response(json.dumps(per_product_response))

    assert result["executive_summary"] == "Summary."


# ---------------------------------------------------------------------
# AIService.generate (parameterized schema)
# ---------------------------------------------------------------------

def test_ai_service_requires_sections_argument():

    try:

        AIService.generate("system", "user")

        assert False, "expected TypeError for missing sections"

    except TypeError:

        pass


# ---------------------------------------------------------------------
# AIRecommendationService.generate_executive_summary
# ---------------------------------------------------------------------

def test_generate_executive_summary_propagates_missing_key_error():

    original_key = ai_service_module.GEMINI_API_KEY

    original_client = AIService._client

    ai_service_module.GEMINI_API_KEY = None

    AIService._client = None

    try:

        try:

            AIRecommendationService.generate_executive_summary(
                SAMPLE_PAYLOAD
            )

            assert False, "expected ValueError"

        except ValueError as error:

            assert "GEMINI_API_KEY" in str(error)

    finally:

        ai_service_module.GEMINI_API_KEY = original_key

        AIService._client = original_client


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
