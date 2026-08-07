"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai_insight_panel.py

Description :
Phase 8 / Milestone 4 - Phase 2: the "Generate AI Insight" button,
session-cached result, and rendered sections for one product row.
Shared by pages/recommendations.py and pages/products.py so this
generate-on-demand / cache-across-reruns interaction pattern lives in
exactly one place instead of being duplicated per page.
=============================================================================
"""

import streamlit as st

from ai.config import SECTION_LABELS
from ai.recommendation import AIRecommendationService


def render_ai_insight_panel(
        cache_key: tuple,
        row: dict | None,
        selected_label: str | None,
        empty_message: str,
        heading: str = "🤖 AI Insight"
):
    """
    Renders the AI Insight section for one row.

    cache_key must uniquely identify the row across reruns (e.g.
    dataset id + product id + store id + the recommendation run's
    timestamp) so switching selection never shows a stale/mismatched
    insight, and a previously generated insight is never regenerated
    (a paid API call) just because Streamlit reran the script.

    row is the exact dict AIRecommendationService.build_payload()
    expects (an InventoryService recommendation row). None renders
    empty_message instead of the button - used when nothing is
    selected yet.
    """

    st.subheader(heading)

    if row is None:

        st.caption(empty_message)

        return

    st.write(f"Selected: {selected_label}")

    generate = st.button(
        "🤖 Generate AI Insight",
        key=f"ai_generate_{cache_key}"
    )

    insights = st.session_state.setdefault("ai_insights", {})

    if generate:

        try:

            with st.spinner("Generating AI insight..."):

                insights[cache_key] = {

                    "ok": True,

                    "data": AIRecommendationService.generate(row)

                }

        except ValueError as error:

            insights[cache_key] = {"ok": False, "error": str(error)}

    cached = insights.get(cache_key)

    if cached is None:

        return

    if cached["ok"]:

        _render_insight(cached["data"])

    else:

        st.error(cached["error"])


def _render_insight(
        insight: dict
):

    for key, label in SECTION_LABELS.items():

        st.markdown(f"**{label}**")

        st.write(insight[key] or "_Not provided by the model._")

    caption_bits = [f"{insight['word_count']} words"]

    if insight["over_word_limit"]:

        caption_bits.append("⚠ over the 250-word guideline")

    if insight["missing_sections"]:

        caption_bits.append(
            "missing: " + ", ".join(insight["missing_sections"])
        )

    st.caption(" · ".join(caption_bits))
