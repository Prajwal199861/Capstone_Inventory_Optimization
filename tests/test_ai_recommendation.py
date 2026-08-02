"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_ai_recommendation.py

Description :
Unit tests for the Phase 8 AI layer's orchestration
(ai/recommendation.py) and the API-call guard (ai/ai_service.py).
No live API calls are made - the missing-key path is exercised by
temporarily clearing the module-level key rather than depending on
whether the environment actually has one configured.

Run with either:
    python tests/test_ai_recommendation.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ai.ai_service as ai_service_module
from ai.ai_service import AIService
from ai.recommendation import AIRecommendationService


SAMPLE_ROW = {

    "Product ID": "P1",

    "Product Name": "Notebook",

    "Category": "Stationery",

    "Season": None,

    "Store ID": "S1",

    "Forecast Demand": 329.6,

    "Demand Change %": -0.7,

    "Current Stock": 194.57,

    "Stock Basis": "Actual",

    "Target Stock Level": 194.57,

    "Recommended Quantity": 0,

    "Days Remaining": 17.7,

    "Status": "Adequate",

    "Risk Level": "Low"

}


def test_build_payload_maps_output_columns_to_ai_fields():

    payload = AIRecommendationService.build_payload(SAMPLE_ROW)

    assert payload["product_name"] == "Notebook"

    assert payload["category"] == "Stationery"

    assert payload["season"] is None

    assert payload["forecasted_demand"] == 329.6

    assert payload["current_inventory"] == 194.57

    assert payload["recommended_inventory"] == 194.57

    assert payload["reorder_quantity"] == 0

    assert payload["stock_status"] == "Adequate"

    assert payload["stockout_risk"] == "Low"

    assert payload["demand_change_pct"] == -0.7


def test_build_payload_tolerates_missing_keys():

    # A row dict missing some columns must not raise - every AI field
    # simply reads as unavailable downstream.
    payload = AIRecommendationService.build_payload({})

    assert payload["product_name"] is None

    assert payload["reorder_quantity"] is None


def test_ai_service_raises_clear_error_without_api_key():

    original_key = ai_service_module.ANTHROPIC_API_KEY

    original_client = AIService._client

    ai_service_module.ANTHROPIC_API_KEY = None

    AIService._client = None

    try:

        try:

            AIService.generate("system", "user")

            assert False, "expected ValueError"

        except ValueError as error:

            assert "ANTHROPIC_API_KEY" in str(error)

    finally:

        ai_service_module.ANTHROPIC_API_KEY = original_key

        AIService._client = original_client


def test_recommendation_generate_propagates_missing_key_error():

    original_key = ai_service_module.ANTHROPIC_API_KEY

    original_client = AIService._client

    ai_service_module.ANTHROPIC_API_KEY = None

    AIService._client = None

    try:

        try:

            AIRecommendationService.generate(SAMPLE_ROW)

            assert False, "expected ValueError"

        except ValueError as error:

            assert "ANTHROPIC_API_KEY" in str(error)

    finally:

        ai_service_module.ANTHROPIC_API_KEY = original_key

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
