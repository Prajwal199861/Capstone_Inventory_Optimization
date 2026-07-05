import streamlit as st
from components.header import page_header
from components.metric_card import metric_card
from components.footer import page_footer

def dashboard():

    page_header(

        "🏠 Dashboard",

        f"Welcome back {st.session_state.full_name}"

    )

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        metric_card("Products", 0)

    with c2:
        metric_card("Datasets", 0)

    with c3:
        metric_card("Forecasts", 0)

    with c4:
        metric_card("Alerts", 0)

    st.divider()

    st.subheader("Quick Actions")

    a,b,c = st.columns(3)

    with a:
        st.button(
            "Upload Dataset",
            use_container_width=True
        )

    with b:
        st.button(
            "Generate Forecast",
            use_container_width=True
        )

    with c:
        st.button(
            "Inventory Report",
            use_container_width=True
        )

    st.info(
        "Milestone 2 will begin with Dataset Management."
    )

    page_footer()