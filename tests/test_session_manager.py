"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_session_manager.py

Description :
Unit tests for auth.session.SessionManager - specifically the
inactivity timeout (SESSION_TIMEOUT_MINUTES was previously declared in
config.py but never enforced anywhere, so a login never expired).
Exercises st.session_state directly; Streamlit supports this outside a
real app run (with a harmless "missing ScriptRunContext" warning).

Run with either:
    python tests/test_session_manager.py
    python -m pytest tests/
=============================================================================
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from config import SESSION_TIMEOUT_MINUTES
from auth.session import SessionManager


class _Role:

    def __init__(self, role_name):

        self.role_name = role_name


class _User:

    def __init__(self):

        self.id = 1

        self.username = "admin"

        self.role = _Role("Admin")

        self.full_name = "System Administrator"


def _reset_session_state():

    for key in (
            "logged_in",
            "user_id",
            "username",
            "role",
            "full_name",
            "last_active"
    ):

        if key in st.session_state:

            del st.session_state[key]


def test_initialize_defaults_last_active_to_none():

    _reset_session_state()

    SessionManager.initialize()

    assert st.session_state["last_active"] is None


def test_initialize_does_not_overwrite_existing_state():

    _reset_session_state()

    SessionManager.initialize()

    marker = datetime.now()

    st.session_state["last_active"] = marker

    SessionManager.initialize()

    assert st.session_state["last_active"] == marker


def test_login_stamps_last_active():

    _reset_session_state()

    SessionManager.login(_User())

    assert st.session_state["logged_in"] is True

    assert isinstance(st.session_state["last_active"], datetime)


def test_is_expired_false_without_a_login():

    _reset_session_state()

    SessionManager.initialize()

    assert SessionManager.is_expired() is False


def test_is_expired_false_within_the_timeout_window():

    _reset_session_state()

    st.session_state["last_active"] = (

        datetime.now()

        - timedelta(minutes=SESSION_TIMEOUT_MINUTES - 1)

    )

    assert SessionManager.is_expired() is False


def test_is_expired_true_past_the_timeout_window():

    _reset_session_state()

    st.session_state["last_active"] = (

        datetime.now()

        - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)

    )

    assert SessionManager.is_expired() is True


def test_touch_resets_the_inactivity_clock():

    _reset_session_state()

    st.session_state["last_active"] = (

        datetime.now()

        - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 5)

    )

    assert SessionManager.is_expired() is True

    SessionManager.touch()

    assert SessionManager.is_expired() is False


def test_logout_clears_last_active():

    _reset_session_state()

    SessionManager.login(_User())

    SessionManager.logout()

    assert "last_active" not in st.session_state

    assert "logged_in" not in st.session_state


# ---------------------------------------------------------------------
# Plain-python runner
# ---------------------------------------------------------------------

if __name__ == "__main__":

    failures = 0

    tests = [

        (name, function)

        for name, function in sorted(globals().items())

        if name.startswith("test_") and callable(function)

    ]

    for name, function in tests:

        try:

            function()

            print(f"PASS  {name}")

        except Exception as error:

            failures += 1

            print(f"FAIL  {name}: {error}")

    print(

        f"\n{len(tests) - failures}/{len(tests)} tests passed."

    )

    sys.exit(1 if failures else 0)
