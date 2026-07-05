"""
=============================================================================
Logout
=============================================================================
"""

import streamlit as st

from auth.session import SessionManager


def logout():

    SessionManager.logout()

    st.rerun()