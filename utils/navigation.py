"""
=============================================================================
Navigation
=============================================================================
"""

import streamlit as st

from auth.logout import logout


def sidebar():

    with st.sidebar:

        st.title("Retail AI")

        st.write(
            f"Welcome, **{st.session_state.full_name}**"
        )

        st.write(
            f"Role : **{st.session_state.role}**"
        )

        st.divider()

        page = st.radio(

            "Navigation",

            [

                "Dashboard",

                "Logout"

            ]

        )

        if page == "Logout":

            logout()

        return page