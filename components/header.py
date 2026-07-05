"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : header.py

Description :
Reusable page header component.
=============================================================================
"""

import streamlit as st


def page_header(
        title: str,
        subtitle: str = ""
):
    """
    Displays a consistent page header.
    """

    st.title(title)

    if subtitle:
        st.caption(subtitle)

    st.divider()