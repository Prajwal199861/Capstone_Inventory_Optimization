"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

Repository : Capstone_Inventory_Optimization

File : app.py

Author : Capstone Group 2

Version : 0.1.0

Description :
Application entry point.

This file initializes the Streamlit application and displays the
landing page. Business logic should not be implemented here.
=============================================================================
"""

import streamlit as st

from config import (
    APP_NAME,
    VERSION,
    AUTHOR
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Home Page
# -----------------------------------------------------------------------------

st.title(APP_NAME)

st.markdown("---")

st.subheader("Welcome")

st.write(
    """
Welcome to the **AI-Powered Retail Demand Forecasting &
Inventory Optimization System**.

This application is being developed as a professional MBA Capstone Project.

The system will help retail businesses:

- Forecast monthly product demand
- Optimize inventory
- Upload and manage multiple datasets
- Generate business reports
- Gain AI-powered business insights
"""
)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Version", VERSION)

with col2:
    st.metric("Status", "Development")

with col3:
    st.metric("Author", AUTHOR)

st.info(
    "Milestone 1 - Foundation & Authentication is currently under development."
)
