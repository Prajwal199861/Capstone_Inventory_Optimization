"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : app.py

Description :
Main entry point of the application.
=============================================================================
"""

import streamlit as st

from config import APP_NAME

from database.init_db import initialize_database

from auth.session import SessionManager
from auth.login import login_page

from utils.navigation import sidebar
from utils.router import route

def load_css():

    with open(
            "assets/css/style.css"
    ) as f:

        st.markdown(

            f"<style>{f.read()}</style>",

            unsafe_allow_html=True

        )

# ---------------------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------------------

st.set_page_config(

    page_title=APP_NAME,

    page_icon="📦",

    layout="wide",

    initial_sidebar_state="expanded"

)

load_css()

initialize_database()

SessionManager.initialize()

# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------

if not st.session_state.logged_in:

    login_page()

    st.stop()

# ---------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------

page = sidebar()

route(page)