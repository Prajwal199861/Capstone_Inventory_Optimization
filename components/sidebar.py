"""
=============================================================================
Sidebar Component
=============================================================================
"""

import streamlit as st


def user_profile():

    with st.container():

        st.success(
            f"👤 {st.session_state.full_name}"
        )

        st.caption(
            f"Role : {st.session_state.role}"
        )

        st.divider()