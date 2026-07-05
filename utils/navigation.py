import streamlit as st

from auth.logout import logout
from components.sidebar import user_profile


def sidebar():

    with st.sidebar:

        st.title("Retail AI")

        st.caption("Inventory Intelligence")

        st.divider()

        user_profile()

        st.divider()

        page = st.radio(

            "",

            [

                "🏠 Dashboard",

                "📂 Datasets",

                "📦 Products",

                "📈 Forecast",

                "🏭 Inventory",

                "📑 Reports",

                "⚙ Administration",

                "🚪 Logout"

            ]

        )

        if page == "🚪 Logout":

            logout()

        return page