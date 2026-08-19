import streamlit as st

from auth.logout import logout
from components.sidebar import user_profile


def sidebar():

    with st.sidebar:

        st.title("Retail AI")

        st.caption("Inventory Intelligence")

        st.divider()

        user_profile()

        page = st.radio(

            "",

            key="navigation",

            options=[

                "🏠 Dashboard",

                "📂 Datasets",

                "📈 Forecast",

                "📦 Products",

                "🏭 Inventory",

                "📑 Reports",

                "🚪 Logout"

            ]

        )

        if page == "🚪 Logout":

            logout()

        return page