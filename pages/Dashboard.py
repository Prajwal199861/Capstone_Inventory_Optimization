"""
=============================================================================
Dashboard
=============================================================================
"""

import streamlit as st


def dashboard():

    st.title("🏠 Dashboard")

    st.success("Successfully Logged In")

    st.write("Welcome")

    st.metric(
        "Logged User",
        st.session_state.full_name
    )

    st.metric(
        "Role",
        st.session_state.role
    )

    st.info(
        "Dashboard development will continue in Milestone 2."
    )