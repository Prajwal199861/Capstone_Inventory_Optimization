"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/utils.py

Description :
Phase 8 - small, pure helpers shared by prompt_builder and formatter.
No API calls, no Streamlit, no database.
=============================================================================
"""

import numbers

from ai.config import NOT_AVAILABLE


def format_value(
        value,
        suffix: str = ""
) -> str:
    """
    Renders a value for the prompt/display, or NOT_AVAILABLE when it
    is missing - the model is told explicitly rather than being handed
    an empty string it might mistake for a real 0.

    Uses numbers.Integral/Real (not isinstance(x, int/float)) so
    numpy scalar types coming out of a pandas row - int64, float64 -
    are recognized too; numpy's integer types do not subclass the
    Python int builtin.
    """

    if value is None:

        return NOT_AVAILABLE

    if isinstance(value, numbers.Real) and not isinstance(
            value,
            numbers.Integral
    ):

        if value != value:  # NaN

            return NOT_AVAILABLE

        text = f"{float(value):,.2f}".rstrip("0").rstrip(".")

    elif isinstance(value, numbers.Integral):

        text = f"{int(value):,}"

    else:

        text = str(value).strip()

        if not text:

            return NOT_AVAILABLE

    return f"{text}{suffix}"


def count_words(
        text: str
) -> int:

    return len(text.split())


def is_over_word_limit(
        sections: dict,
        max_words: int
) -> bool:
    """Total words across every section, against the prompt's own
    stated budget - used to flag (not silently truncate) an
    over-length response."""

    total = sum(
        count_words(text)
        for text in sections.values()
        if isinstance(text, str)
    )

    return total > max_words
