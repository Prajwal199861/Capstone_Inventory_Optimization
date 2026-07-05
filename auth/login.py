"""
=============================================================================
Login Screen
=============================================================================
"""

import streamlit as st

from auth.session import SessionManager
from services.authentication_service import AuthenticationService


def login_page():

    st.title("🔐 Login")

    st.markdown("### AI-Powered Retail Demand Forecasting & Inventory Optimization")

    username = st.text_input("Username")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
            "Login",
            use_container_width=True
    ):

        user = AuthenticationService.login(
            username,
            password
        )

        if user:

            SessionManager.login(user)

            st.success("Login Successful")

            st.rerun()

        else:

            st.error("Invalid Username or Password")