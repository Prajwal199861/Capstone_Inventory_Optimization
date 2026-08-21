"""
=============================================================================
Session Manager
=============================================================================
"""

from datetime import datetime, timedelta

import streamlit as st

from config import SESSION_TIMEOUT_MINUTES


class SessionManager:

    @staticmethod
    def initialize():

        defaults = {

            "logged_in": False,

            "user_id": None,

            "username": None,

            "role": None,

            "full_name": None,

            "last_active": None

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

        st.session_state.last_active = datetime.now()

    @staticmethod
    def logout():

        keys = [

            "logged_in",

            "user_id",

            "username",

            "role",

            "full_name",

            "last_active"

        ]

        for key in keys:

            if key in st.session_state:

                del st.session_state[key]

    @staticmethod
    def is_expired() -> bool:
        """
        True once more than SESSION_TIMEOUT_MINUTES has passed since
        the last page load/interaction this user made. Must be called
        BEFORE touch() on every rerun, while "last_active" still holds
        the time of the previous interaction rather than this one.
        """

        last_active = st.session_state.get("last_active")

        if last_active is None:

            return False

        elapsed = datetime.now() - last_active

        return elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    @staticmethod
    def touch():
        """Records this interaction as the session's most recent
        activity, resetting the inactivity clock."""

        st.session_state.last_active = datetime.now()