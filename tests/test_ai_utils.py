"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_ai_utils.py

Description :
Unit tests for the Phase 8 AI layer's small pure helpers
(ai/utils.py). No API calls, no database.

Run with either:
    python tests/test_ai_utils.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from ai.config import NOT_AVAILABLE
from ai.utils import count_words, format_value, is_over_word_limit


def test_format_value_none_is_not_available():

    assert format_value(None) == NOT_AVAILABLE


def test_format_value_nan_is_not_available():

    assert format_value(float("nan")) == NOT_AVAILABLE


def test_format_value_formats_float_trimmed():

    assert format_value(194.50) == "194.5"

    assert format_value(194.0) == "194"


def test_format_value_formats_int_with_thousands_separator():

    assert format_value(15000) == "15,000"


def test_format_value_handles_numpy_scalars():

    # numpy.int64 does not subclass Python int - a real footgun this
    # module must not fall over on, since pandas rows hand these back.
    assert format_value(np.int64(0)) == "0"

    assert format_value(np.int64(15000)) == "15,000"

    assert format_value(np.float64(194.567)) == "194.57"


def test_format_value_string_passthrough():

    assert format_value("Low") == "Low"

    assert format_value("  ") == NOT_AVAILABLE


def test_format_value_applies_suffix_to_numbers_only():

    assert format_value(-3.6, "%") == "-3.6%"


def test_count_words():

    assert count_words("one two three") == 3

    assert count_words("") == 0


def test_is_over_word_limit():

    sections = {"a": "one two three", "b": "four five"}

    assert is_over_word_limit(sections, 4) is True

    assert is_over_word_limit(sections, 5) is False

    assert is_over_word_limit(sections, 10) is False


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
