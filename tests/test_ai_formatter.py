"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_ai_formatter.py

Description :
Unit tests for the Phase 8 AI layer's response parsing
(ai/formatter.py). Pure JSON parsing/validation - no API calls.

Run with either:
    python tests/test_ai_formatter.py
    python -m pytest tests/
=============================================================================
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.formatter import format_response


FULL_RESPONSE = {

    "executive_summary": "Notebook demand is stable this cycle.",

    "business_recommendation": "Maintain the current ordering cadence.",

    "inventory_action": "No reorder is needed this cycle.",

    "risk_explanation": "Stock-out risk is low given the buffer.",

    "final_recommendation": "Recheck after the next forecast run."

}


def test_parses_valid_json():

    result = format_response(json.dumps(FULL_RESPONSE))

    for key, text in FULL_RESPONSE.items():

        assert result[key] == text

    assert result["missing_sections"] == []

    assert result["word_count"] > 0

    assert result["over_word_limit"] is False


def test_strips_markdown_code_fence():

    fenced = "```json\n" + json.dumps(FULL_RESPONSE) + "\n```"

    result = format_response(fenced)

    assert result["executive_summary"] == (
        FULL_RESPONSE["executive_summary"]
    )


def test_missing_keys_default_to_empty_and_are_reported():

    partial = json.dumps({"executive_summary": "Only this one."})

    result = format_response(partial)

    assert result["executive_summary"] == "Only this one."

    assert result["business_recommendation"] == ""

    assert "Business Recommendation" in result["missing_sections"]

    assert "Final Recommendation" in result["missing_sections"]

    assert len(result["missing_sections"]) == 4


def test_invalid_json_raises_value_error():

    try:

        format_response("this is not json")

        assert False, "expected ValueError"

    except ValueError:

        pass


def test_non_object_json_raises_value_error():

    try:

        format_response("[1, 2, 3]")

        assert False, "expected ValueError"

    except ValueError:

        pass


def test_over_word_limit_flagged_not_truncated():

    long_text = " ".join(["word"] * 300)

    response = dict(FULL_RESPONSE)

    response["executive_summary"] = long_text

    result = format_response(json.dumps(response))

    assert result["over_word_limit"] is True

    # The model's own wording is never mangled/cut mid-sentence.
    assert result["executive_summary"] == long_text


def test_blank_string_value_counts_as_missing():

    response = dict(FULL_RESPONSE)

    response["risk_explanation"] = "   "

    result = format_response(json.dumps(response))

    assert result["risk_explanation"] == ""

    assert "Risk Explanation" in result["missing_sections"]


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
