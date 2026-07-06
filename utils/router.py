"""
=============================================================================
Router
=============================================================================
"""

import streamlit as st

from pages.dashboard import dashboard
from pages.dataset_management import dataset_management


def route(page):

    routes = {

        "🏠 Dashboard": dashboard,

        "📂 Datasets": dataset_management,

    }

    if page in routes:

        routes[page]()

    else:

        st.info(
            f"{page} module will be available in upcoming milestones."
        )