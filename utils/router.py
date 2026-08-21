"""
=============================================================================
Router
=============================================================================
"""

import streamlit as st

from app_pages.dashboard import dashboard
from app_pages.dataset_management import dataset_management
from app_pages.dataset_details import dataset_details
from app_pages.standardized_preview import standardized_preview
from app_pages.forecast import forecast
from app_pages.inventory_dashboard import inventory_dashboard
from app_pages.products import products
from app_pages.reports import reports


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

        "📦 Products": products,

        "📈 Forecast": forecast,

        "🏭 Inventory": inventory_dashboard,

        "📑 Reports": reports,

    }

    if page in routes:

        routes[page]()

    else:

        st.info(
            f"{page} module will be available in upcoming milestones."
        )