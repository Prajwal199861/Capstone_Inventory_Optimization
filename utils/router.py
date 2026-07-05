"""
=============================================================================
Router
=============================================================================
"""

from pages.Dashboard import dashboard

import streamlit as st


def route(page):

    if page == "🏠 Dashboard":

        dashboard()

    else:

        st.info(

            f"{page} will be available in upcoming milestones."

        )