import streamlit as st

from auth.session import SessionManager

from services.authentication_service import AuthenticationService


def login_page():

    left, center, right = st.columns([1,2,1])

    with center:

        st.markdown("<br><br>",unsafe_allow_html=True)

        st.title("Retail AI")

        st.caption(
            "Demand Forecasting & Inventory Optimization"
        )

        st.divider()

        username = st.text_input(
            "Username"
        )

        password = st.text_input(

            "Password",

            type="password"

        )

        if st.button(

                "LOGIN",

                use_container_width=True

        ):

            user = AuthenticationService.login(

                username,

                password

            )

            if user:

                SessionManager.login(user)

                st.rerun()

            st.error(

                "Invalid username or password."

            )