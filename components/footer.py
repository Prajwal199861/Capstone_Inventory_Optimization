"""
=============================================================================
Footer Component
=============================================================================
"""

import streamlit as st

from config import VERSION


def page_footer():

    st.divider()

    left, right = st.columns([3, 1])

    with left:

        st.caption(
            "AI-Powered Retail Demand Forecasting & Inventory Optimization"
        )

    with right:

        st.caption(
            f"Version {VERSION}"
        )