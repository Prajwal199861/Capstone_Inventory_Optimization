"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/formatter.py

Description :
Phase 8 - turns the model's raw text response into the structured
insight the UI displays: parses the JSON, validates it carries the
five required sections, and flags (without silently mangling the
model's wording) if it ran over the prompt's own word budget.
=============================================================================
"""

import json
import re

from ai.config import (
    AI_MAX_RESPONSE_WORDS,
    INSIGHT_SECTIONS,
    SECTION_LABELS
)

from ai.utils import count_words, is_over_word_limit


_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _strip_code_fence(
        text: str
) -> str:
    """Models occasionally wrap JSON in a ```json fence despite being
    told not to; strip it rather than fail the whole response."""

    return _CODE_FENCE.sub("", text.strip()).strip()


def format_response(
        raw_text: str
) -> dict:
    """
    Parses and validates one model response.

    Returns:

        {
            "executive_summary": str,
            "business_recommendation": str,
            "inventory_action": str,
            "risk_explanation": str,
            "final_recommendation": str,
            "missing_sections": [str],
            "word_count": int,
            "over_word_limit": bool
        }

    Raises ValueError when the response isn't valid JSON at all - a
    surfaced, retryable failure is better than silently showing junk.
    Individual missing keys are tolerated (defaulted to "") and
    reported via "missing_sections" rather than failing the whole
    insight over one dropped field.
    """

    cleaned = _strip_code_fence(raw_text)

    try:

        parsed = json.loads(cleaned)

    except json.JSONDecodeError as error:

        raise ValueError(

            "AI insight failed: the model's response could not be "

            "parsed. Please try again."

        ) from error

    if not isinstance(parsed, dict):

        raise ValueError(

            "AI insight failed: the model's response was not the "

            "expected JSON object. Please try again."

        )

    sections = {}

    missing_sections = []

    for key in INSIGHT_SECTIONS:

        value = parsed.get(key)

        if isinstance(value, str) and value.strip():

            sections[key] = value.strip()

        else:

            sections[key] = ""

            missing_sections.append(SECTION_LABELS[key])

    word_count = sum(
        count_words(text) for text in sections.values()
    )

    return {

        **sections,

        "missing_sections": missing_sections,

        "word_count": word_count,

        "over_word_limit": is_over_word_limit(
            sections,
            AI_MAX_RESPONSE_WORDS
        )

    }
