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


_SNIPPET_LIMIT = 600


def _snippet(
        text: str
) -> str:
    """Truncated raw response for error messages - enough to diagnose
    what the model actually sent without an unwieldy UI error box."""

    text = text.strip()

    if len(text) <= _SNIPPET_LIMIT:

        return repr(text)

    return repr(text[:_SNIPPET_LIMIT]) + f"... ({len(text)} chars total)"


def format_response(
        raw_text: str,
        sections: list[str] = INSIGHT_SECTIONS,
        section_labels: dict = SECTION_LABELS,
        max_words: int = AI_MAX_RESPONSE_WORDS
) -> dict:
    """
    Parses and validates one model response against a given JSON
    contract (defaults to the per-product AI Insight's five sections;
    the AI Executive Report passes its own `sections`/
    `section_labels`/`max_words` - see ai/config.py).

    Returns:

        {
            <one key per entry in `sections`>: str,
            "missing_sections": [str],
            "word_count": int,
            "over_word_limit": bool
        }

    Raises ValueError when the response isn't valid JSON at all - a
    surfaced, retryable failure is better than silently showing junk.
    Individual missing keys are tolerated (defaulted to "") and
    reported via "missing_sections" rather than failing the whole
    response over one dropped field.
    """

    cleaned = _strip_code_fence(raw_text)

    try:

        parsed = json.loads(cleaned)

    except json.JSONDecodeError as error:

        raise ValueError(

            "AI insight failed: the model's response could not be "

            "parsed. Please try again. Raw response: "

            f"{_snippet(raw_text)}"

        ) from error

    if not isinstance(parsed, dict):

        raise ValueError(

            "AI insight failed: the model's response was not the "

            "expected JSON object. Please try again. Raw response: "

            f"{_snippet(raw_text)}"

        )

    result_sections = {}

    missing_sections = []

    for key in sections:

        value = parsed.get(key)

        if isinstance(value, str) and value.strip():

            result_sections[key] = value.strip()

        else:

            result_sections[key] = ""

            missing_sections.append(section_labels[key])

    word_count = sum(
        count_words(text) for text in result_sections.values()
    )

    return {

        **result_sections,

        "missing_sections": missing_sections,

        "word_count": word_count,

        "over_word_limit": is_over_word_limit(
            result_sections,
            max_words
        )

    }
