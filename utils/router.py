"""
=============================================================================
Router
=============================================================================
"""

import streamlit as st

from pages.dashboard import dashboard
from pages.dataset_management import dataset_management
from pages.dataset_details import dataset_details


def route(page):
    if (

            st.session_state.get(

                "current_page"

            )

            ==

            "dataset_details"

    ):
        dataset_details()

        return
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