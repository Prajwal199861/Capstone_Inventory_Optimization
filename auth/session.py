"""
=============================================================================
Session Manager
=============================================================================
"""

import streamlit as st


class SessionManager:

    @staticmethod
    def initialize():

        defaults = {

            "logged_in": False,

            "user_id": None,

            "username": None,

            "role": None,

            "full_name": None

        }

        for key, value in defaults.items():

            if key not in st.session_state:

                st.session_state[key] = value

    @staticmethod
    def login(user):

        st.session_state.logged_in = True

        st.session_state.user_id = user.id

        st.session_state.username = user.username

        st.session_state.role = user.role.role_name

        st.session_state.full_name = user.full_name

    @staticmethod
    def logout():

        keys = [

            "logged_in",

            "user_id",

            "username",

            "role",

            "full_name"

        ]

        for key in keys:

            if key in st.session_state:

                del st.session_state[key]