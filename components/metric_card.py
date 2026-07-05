"""
=============================================================================
Metric Card Component
=============================================================================
"""

import streamlit as st


def metric_card(
        title: str,
        value,
        delta=None
):
    """
    Reusable KPI card.
    """

    st.metric(

        label=title,

        value=value,

        delta=delta

    )