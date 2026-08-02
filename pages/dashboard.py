import streamlit as st
from components.header import page_header
from components.metric_card import metric_card
from components.footer import page_footer
from services.dataset_service import DatasetService
from services.demand_service import DemandService
from services.forecast_service import ForecastService
from services.inventory_service import InventoryService


@st.cache_data(ttl=300, show_spinner=False)
def _count_products(ready_dataset_ids: tuple) -> int:
    """Distinct products across READY datasets (cached: loads files)."""

    product_ids = set()

    for dataset_id in ready_dataset_ids:

        try:

            options = DemandService.get_filter_options(dataset_id)

            product_ids.update(
                str(product_id)
                for product_id, _ in options["products"]
            )

        except Exception:

            continue

    return len(product_ids)


@st.cache_data(ttl=300, show_spinner=False)
def _count_alerts(ready_dataset_ids: tuple) -> int:
    """Critical-risk recommendations across READY datasets that have
    an Inventory file and a batch forecast (cached: recomputes
    inventory optimization). Datasets missing either are skipped
    silently - they simply contribute no alerts yet."""

    alerts = 0

    for dataset_id in ready_dataset_ids:

        try:

            result = InventoryService.generate_recommendations(
                dataset_id
            )

            alerts += int(
                (
                    result["recommendations"]["Risk Level"] == "Critical"
                ).sum()
            )

        except ValueError:

            continue

        except Exception:

            continue

    return alerts


def _navigate_to(page: str):

    st.session_state.pop("current_page", None)

    st.session_state.navigation = page


def dashboard():

    page_header(

        "🏠 Dashboard",

        f"Welcome back {st.session_state.full_name}"

    )

    ready_ids = tuple(

        dataset.id

        for dataset in DemandService.get_ready_datasets()

    )

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        metric_card("Products", _count_products(ready_ids))

    with c2:
        metric_card("Datasets", DatasetService.count_datasets())

    with c3:
        metric_card("Forecasts", ForecastService.count_forecasts())

    with c4:
        metric_card("Alerts", _count_alerts(ready_ids))

    st.divider()

    st.subheader("Quick Actions")

    a,b,c = st.columns(3)

    with a:
        st.button(
            "Upload Dataset",
            use_container_width=True,
            on_click=_navigate_to,
            args=("📂 Datasets",)
        )

    with b:
        st.button(
            "Generate Forecast",
            use_container_width=True,
            on_click=_navigate_to,
            args=("📈 Forecast",)
        )

    with c:
        st.button(
            "Inventory Report",
            use_container_width=True,
            on_click=_navigate_to,
            args=("🏭 Inventory",)
        )

    st.info(
        "Milestone 3: demand forecasting and inventory optimization "
        "are live — upload a dataset, complete its column mapping, "
        "generate a batch forecast, then run inventory optimization."
    )

    page_footer()
