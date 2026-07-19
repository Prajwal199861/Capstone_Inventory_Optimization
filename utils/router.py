"""
=============================================================================
Router
=============================================================================
"""

import streamlit as st

from pages.dashboard import dashboard
from pages.dataset_management import dataset_management
from pages.dataset_details import dataset_details
from pages.standardized_preview import standardized_preview
from pages.forecast import forecast


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

    if (

            st.session_state.get(

                "current_page"

            )

            ==

            "standardized_preview"

    ):
        standardized_preview()

        return
    routes = {

        "🏠 Dashboard": dashboard,

        "📂 Datasets": dataset_management,

        "📈 Forecast": forecast,

    }

    if page in routes:

        routes[page]()

    else:

        st.info(
            f"{page} module will be available in upcoming milestones."
        )