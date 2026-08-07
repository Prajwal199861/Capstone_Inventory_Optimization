"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : reports.py

Description :
Milestone 4 - Phase 3: Reports & Business Intelligence.

Five report categories over one dataset - Executive Dashboard
(default), Inventory Report, Forecast Report, Product Performance
Report, AI Executive Report - each with CSV/Excel/PDF export, plus a
combined multi-sheet workbook export. No business logic lives here;
everything is computed by ReportService / report_charts /
report_export. Forecasting, inventory optimization and the AI call
only ever run when the user explicitly triggers them (batch forecast
on the Forecast page, and the "Generate Executive Summary" button
below) - every report here reads from the one already-loaded,
per-dataset-cached bundle.
=============================================================================
"""

from datetime import datetime

import streamlit as st

from components.header import page_header
from components.footer import page_footer
from components.metric_card import metric_card

from ai.config import EXECUTIVE_SECTION_LABELS
from ai.recommendation import AIRecommendationService

from services.demand_service import DemandService
from services.report_service import ReportService

from utils import report_charts as charts
from utils import report_export as export
from utils.inventory_metrics import InventoryMetrics


REPORT_CATEGORIES = [

    "Executive Dashboard",

    "Inventory Report",

    "Forecast Report",

    "Product Performance Report",

    "AI Executive Report"

]

ALL_OPTION = "All"

EXCEL_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@st.cache_data(ttl=300, show_spinner=False)
def _load_bundle(
        dataset_id: int
):
    """The one expensive pass, cached per dataset across every rerun
    this page triggers (changing report category, adjusting a
    filter) - forecasting/optimization never re-run just because the
    user interacted with a widget."""

    return ReportService.load_dataset(dataset_id)


def _kpi_value(
        value,
        prefix: str = ""
) -> str:

    if value is None:

        return "n/a"

    if isinstance(value, (int, float)):

        return f"{prefix}{value:,.0f}"

    return f"{prefix}{value}"


def _export_row(
        report_key: str,
        report_title: str,
        dataset_id: int,
        dataset_name: str,
        generated_at: datetime,
        export_table,
        kpis: dict | None = None,
        chart_figures: list | None = None,
        pdf_tables: list | None = None,
        summary_sections: dict | None = None
):
    """CSV / Excel / PDF export buttons for whichever report is
    currently on screen."""

    st.markdown("**⬇ Export This Report**")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.download_button(

            "⬇ CSV",

            export.to_csv_bytes(export_table),

            file_name=f"{report_key}_dataset_{dataset_id}.csv",

            mime="text/csv",

            use_container_width=True,

            key=f"{report_key}_csv"

        )

    with c2:

        st.download_button(

            "⬇ Excel",

            export.to_excel_bytes({report_title[:31]: export_table}),

            file_name=f"{report_key}_dataset_{dataset_id}.xlsx",

            mime=EXCEL_MIME,

            use_container_width=True,

            key=f"{report_key}_excel"

        )

    with c3:

        pdf_bytes = export.build_pdf_bytes(

            title=report_title,

            dataset_name=dataset_name,

            generated_at=generated_at,

            kpis=kpis,

            charts=chart_figures,

            tables=pdf_tables or [(report_title, export_table)],

            summary_sections=summary_sections

        )

        st.download_button(

            "⬇ PDF",

            pdf_bytes,

            file_name=f"{report_key}_dataset_{dataset_id}.pdf",

            mime="application/pdf",

            use_container_width=True,

            key=f"{report_key}_pdf"

        )


# -----------------------------------------------------------------
# 1. Executive Dashboard Report
# -----------------------------------------------------------------

def _executive_dashboard(
        bundle: dict,
        dataset_id: int,
        dataset_name: str,
        generated_at: datetime
):

    data = ReportService.executive_summary(bundle)

    kpis = data["kpis"]

    r1 = st.columns(4)

    with r1[0]:

        metric_card("Products", kpis["total_products"])

    with r1[1]:

        metric_card("Forecasted Products", kpis["forecasted_products"])

    with r1[2]:

        metric_card("Critical Risk", kpis["critical_risk"])

    with r1[3]:

        metric_card("High Risk", kpis["high_risk"])

    r2 = st.columns(4)

    with r2[0]:

        metric_card(
            "Inventory Value",
            _kpi_value(kpis["inventory_value"], prefix="$")
        )

    with r2[1]:

        metric_card(
            "Forecast Horizon",
            _kpi_value(kpis["forecast_horizon"])
        )

    with r2[2]:

        metric_card("Forecast Model", kpis["forecast_model"] or "n/a")

    with r2[3]:

        metric_card("Generated", generated_at.strftime("%Y-%m-%d"))

    st.divider()

    fig_risk = charts.risk_pie_chart(data["risk_distribution"])

    fig_category_demand = charts.category_bar_chart(

        data["forecast_demand_by_category"],

        "Category",

        "Forecast Demand",

        title="Forecast Demand by Category",

        ylabel="Units"

    )

    fig_category_value = charts.category_bar_chart(

        data["inventory_value_by_category"],

        "Category",

        "Inventory Value",

        title="Inventory Value by Category",

        ylabel="$"

    )

    fig_top_demand = charts.top_products_bar_chart(

        data["top_products_by_demand"],

        "Product Name",

        "Forecast Demand",

        title="Top 10 Products by Forecast Demand",

        xlabel="Units"

    )

    c1, c2 = st.columns(2)

    with c1:

        st.pyplot(fig_risk)

    with c2:

        st.pyplot(fig_category_demand)

    c3, c4 = st.columns(2)

    with c3:

        st.pyplot(fig_category_value)

    with c4:

        st.pyplot(fig_top_demand)

    st.divider()

    pdf_kpis = {

        "Total Products": kpis["total_products"],

        "Forecasted Products": kpis["forecasted_products"],

        "Critical Risk": kpis["critical_risk"],

        "High Risk": kpis["high_risk"],

        "Inventory Value": _kpi_value(
            kpis["inventory_value"], prefix="$"
        ),

        "Forecast Horizon": _kpi_value(kpis["forecast_horizon"]),

        "Forecast Model": kpis["forecast_model"] or "n/a"

    }

    _export_row(

        "executive_dashboard",

        "Executive Dashboard Report",

        dataset_id,

        dataset_name,

        generated_at,

        export_table=data["top_products_by_demand"],

        kpis=pdf_kpis,

        chart_figures=[

            ("Inventory Risk Distribution", fig_risk),

            ("Forecast Demand by Category", fig_category_demand),

            ("Inventory Value by Category", fig_category_value),

            ("Top 10 Products by Forecast Demand", fig_top_demand)

        ],

        pdf_tables=[

            ("Top 10 Products by Forecast Demand",
             data["top_products_by_demand"])

        ]

    )


# -----------------------------------------------------------------
# 2. Inventory Report
# -----------------------------------------------------------------

_INVENTORY_DISPLAY_COLUMNS = [

    "Product ID",

    "Product Name",

    "Category",

    "Store ID",

    "Current Stock",

    "Forecast Demand",

    "Safety Stock",

    "Reorder Point",

    "Recommended Quantity",

    "Risk Level",

    "Status",

    "Reason"

]


def _inventory_report(
        bundle: dict,
        dataset_id: int,
        dataset_name: str,
        generated_at: datetime
):

    recommendations = bundle["recommendations"]

    if recommendations.empty:

        st.info("No Inventory Available for this dataset.")

        return

    f1, f2, f3, f4 = st.columns(4)

    with f1:

        store = st.selectbox(

            "Store",

            [ALL_OPTION] + sorted(
                recommendations["Store ID"].dropna().unique().tolist()
            )

        )

    with f2:

        category_options = (

            sorted(
                recommendations["Category"].dropna().unique().tolist()
            )

            if "Category" in recommendations.columns

            else []

        )

        category = st.selectbox("Category", [ALL_OPTION] + category_options)

    with f3:

        risk = st.selectbox(
            "Risk", [ALL_OPTION, "Critical", "High", "Medium", "Low"]
        )

    with f4:

        product = st.selectbox(

            "Product",

            [ALL_OPTION] + sorted(
                recommendations["Product Name"].dropna().unique().tolist()
            )

        )

    filtered = recommendations

    if store != ALL_OPTION:

        filtered = filtered[filtered["Store ID"] == store]

    if category != ALL_OPTION:

        filtered = filtered[filtered["Category"] == category]

    if risk != ALL_OPTION:

        filtered = filtered[filtered["Risk Level"] == risk]

    if product != ALL_OPTION:

        filtered = filtered[filtered["Product Name"] == product]

    display_columns = [

        column
        for column in _INVENTORY_DISPLAY_COLUMNS
        if column in filtered.columns

    ]

    st.caption(
        f"Showing {len(filtered):,} of {len(recommendations):,} "
        f"row(s)."
    )

    st.dataframe(

        filtered[display_columns],

        use_container_width=True,

        hide_index=True

    )

    st.divider()

    totals = ReportService.inventory_position_totals(filtered)

    risk_distribution = InventoryMetrics.risk_breakdown(filtered)

    fig_position = charts.inventory_position_chart(totals)

    fig_risk = charts.risk_pie_chart(
        risk_distribution,
        title="Risk Distribution"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.pyplot(fig_position)

    with c2:

        st.pyplot(fig_risk)

    st.divider()

    _export_row(

        "inventory_report",

        "Inventory Report",

        dataset_id,

        dataset_name,

        generated_at,

        export_table=filtered[display_columns],

        kpis=totals,

        chart_figures=[

            ("Inventory Position", fig_position),

            ("Risk Distribution", fig_risk)

        ],

        pdf_tables=[("Inventory Detail", filtered[display_columns])]

    )


# -----------------------------------------------------------------
# 3. Forecast Report
# -----------------------------------------------------------------

def _forecast_report(
        bundle: dict,
        dataset_id: int,
        dataset_name: str,
        generated_at: datetime
):

    data = ReportService.forecast_report(bundle, dataset_id)

    meta = data["meta"]

    if meta is None:

        st.warning("No Forecast Available for this dataset.")

        return

    r1 = st.columns(4)

    with r1[0]:

        metric_card("Forecast Model", meta["model_name"])

    with r1[1]:

        metric_card("Horizon", meta["horizon"])

    with r1[2]:

        metric_card("Granularity", meta["granularity"])

    with r1[3]:

        metric_card("Products Forecasted", data["products_forecasted"])

    lower, upper = data["confidence_range"]

    caption_bits = [
        f"Forecast Date: {meta['created_at']:%Y-%m-%d %H:%M}"
    ]

    if lower is not None:

        caption_bits.append(

            f"Confidence Interval (total): {lower:,.0f} - {upper:,.0f}"

        )

    st.caption(" · ".join(caption_bits))

    for note in data["notes"]:

        st.caption(f"ℹ {note}")

    st.divider()

    fig_trend = charts.forecast_trend_chart(

        data["trend"],

        history=None,

        measure=meta["measure"],

        title="Forecast Trend"

    )

    fig_vs_history = charts.forecast_trend_chart(

        data["trend"],

        history=data["history"],

        measure=meta["measure"],

        title="Forecast vs Historical"

    )

    fig_demand_by_product = charts.top_products_bar_chart(

        data["demand_by_product"],

        "Product Name",

        "Forecast Demand",

        title="Demand by Product",

        xlabel=meta["measure"]

    )

    st.pyplot(fig_trend)

    c1, c2 = st.columns(2)

    with c1:

        st.pyplot(fig_vs_history)

    with c2:

        st.pyplot(fig_demand_by_product)

    st.divider()

    st.dataframe(data["table"], use_container_width=True, hide_index=True)

    st.divider()

    pdf_kpis = {

        "Forecast Model": meta["model_name"],

        "Horizon": meta["horizon"],

        "Granularity": meta["granularity"],

        "Products Forecasted": data["products_forecasted"],

        "Forecast Date": f"{meta['created_at']:%Y-%m-%d %H:%M}"

    }

    _export_row(

        "forecast_report",

        "Forecast Report",

        dataset_id,

        dataset_name,

        generated_at,

        export_table=data["table"],

        kpis=pdf_kpis,

        chart_figures=[

            ("Forecast Trend", fig_trend),

            ("Forecast vs Historical", fig_vs_history),

            ("Demand by Product", fig_demand_by_product)

        ],

        pdf_tables=[("Forecast by Product", data["table"])]

    )


# -----------------------------------------------------------------
# 4. Product Performance Report
# -----------------------------------------------------------------

def _product_performance_report(
        bundle: dict,
        dataset_id: int,
        dataset_name: str,
        generated_at: datetime
):

    if bundle["products"].empty:

        st.info("No product data available for this dataset.")

        return

    data = ReportService.product_performance_report(bundle)

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("**📈 Top Growing Products**")

        st.dataframe(
            data["top_growing"],
            use_container_width=True,
            hide_index=True
        )

    with c2:

        st.markdown("**📉 Top Declining Products**")

        st.dataframe(
            data["top_declining"],
            use_container_width=True,
            hide_index=True
        )

    c3, c4 = st.columns(2)

    with c3:

        st.markdown("**💰 Highest Inventory Value**")

        st.dataframe(
            data["highest_inventory_value"],
            use_container_width=True,
            hide_index=True
        )

    with c4:

        st.markdown("**🔥 Highest Forecast Demand**")

        st.dataframe(
            data["highest_forecast_demand"],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("**🔴 Critical Products**")

    st.dataframe(
        data["critical_products"],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    fig_top20 = charts.top_products_bar_chart(

        data["top20_demand"],

        "Product Name",

        "Forecast Demand",

        title="Top 20 Demand"

    )

    fig_category = charts.category_bar_chart(

        data["category_performance"],

        "Category",

        "Forecast Demand",

        title="Category Performance",

        ylabel="Units"

    )

    fig_inventory_value = charts.top_products_bar_chart(

        data["highest_inventory_value"],

        "Product Name",

        "Inventory Value",

        title="Inventory Value (Top 10)",

        xlabel="$"

    )

    st.pyplot(fig_top20)

    c5, c6 = st.columns(2)

    with c5:

        st.pyplot(fig_category)

    with c6:

        st.pyplot(fig_inventory_value)

    st.divider()

    _export_row(

        "product_performance_report",

        "Product Performance Report",

        dataset_id,

        dataset_name,

        generated_at,

        export_table=bundle["products"],

        chart_figures=[

            ("Top 20 Demand", fig_top20),

            ("Category Performance", fig_category),

            ("Inventory Value (Top 10)", fig_inventory_value)

        ],

        pdf_tables=[

            ("Top Growing Products", data["top_growing"]),

            ("Top Declining Products", data["top_declining"]),

            ("Highest Inventory Value", data["highest_inventory_value"]),

            (
                "Highest Forecast Demand",
                data["highest_forecast_demand"]
            ),

            ("Critical Products", data["critical_products"])

        ]

    )


# -----------------------------------------------------------------
# 5. AI Executive Report
# -----------------------------------------------------------------

def _ai_executive_report(
        bundle: dict,
        dataset_id: int,
        dataset_name: str,
        generated_at: datetime
):

    st.caption(

        "Gemini summarizes overall inventory health, critical "

        "products, overstock/stockout risks and recommended "

        "management actions from the numbers already computed above "

        "- it does not calculate anything itself."

    )

    generate = st.button(
        "🤖 Generate Executive Summary",
        type="primary"
    )

    meta = bundle["forecast_meta"]

    cache_key = (

        dataset_id,

        "ai_executive",

        str(meta["created_at"]) if meta else "none"

    )

    cache = st.session_state.setdefault("ai_executive_summaries", {})

    if generate:

        payload = ReportService.ai_executive_payload(bundle, dataset_name)

        try:

            with st.spinner("Generating executive summary..."):

                cache[cache_key] = {

                    "ok": True,

                    "data": (

                        AIRecommendationService

                        .generate_executive_summary(payload)

                    )

                }

        except ValueError as error:

            cache[cache_key] = {"ok": False, "error": str(error)}

    cached = cache.get(cache_key)

    if cached is None:

        st.info(
            "Click **Generate Executive Summary** to create an "
            "AI-written summary of this dataset."
        )

        return

    if not cached["ok"]:

        st.error(cached["error"])

        return

    data = cached["data"]

    for key, label in EXECUTIVE_SECTION_LABELS.items():

        st.markdown(f"**{label}**")

        st.write(data[key] or "_Not provided by the model._")

    caption_bits = [f"{data['word_count']} words"]

    if data["over_word_limit"]:

        caption_bits.append("⚠ over the 400-word guideline")

    if data["missing_sections"]:

        caption_bits.append(
            "missing: " + ", ".join(data["missing_sections"])
        )

    st.caption(" · ".join(caption_bits))

    st.divider()

    summary_sections = {

        label: data[key]

        for key, label in EXECUTIVE_SECTION_LABELS.items()

    }

    st.markdown("**⬇ Export This Report**")

    pdf_bytes = export.build_pdf_bytes(

        title="AI Executive Report",

        dataset_name=dataset_name,

        generated_at=generated_at,

        summary_sections=summary_sections

    )

    st.download_button(

        "⬇ PDF",

        pdf_bytes,

        file_name=f"ai_executive_report_dataset_{dataset_id}.pdf",

        mime="application/pdf",

        key="ai_executive_pdf"

    )


# -----------------------------------------------------------------
# Page entry point
# -----------------------------------------------------------------

def reports():

    page_header(

        "📑 Reports",

        "Business intelligence consolidated from forecasting, "

        "inventory optimization, product intelligence and AI "

        "insights."

    )

    datasets = DemandService.get_ready_datasets()

    if not datasets:

        st.info(

            "No READY datasets found. Upload a dataset and complete "

            "its column mapping first."

        )

        page_footer()

        return

    dataset_labels = {

        f"{dataset.dataset_name} (id {dataset.id})": dataset.id

        for dataset in datasets

    }

    c1, c2 = st.columns(2)

    with c1:

        selected = st.selectbox("Dataset", list(dataset_labels.keys()))

    dataset_id = dataset_labels[selected]

    dataset_name = selected.rsplit(" (id ", 1)[0]

    with c2:

        category = st.selectbox("Report Category", REPORT_CATEGORIES)

    try:

        bundle = _load_bundle(dataset_id)

    except ValueError as error:

        st.warning(str(error))

        page_footer()

        return

    for note in bundle["notes"]:

        st.caption(f"ℹ {note}")

    st.divider()

    generated_at = datetime.now()

    renderers = {

        "Executive Dashboard": _executive_dashboard,

        "Inventory Report": _inventory_report,

        "Forecast Report": _forecast_report,

        "Product Performance Report": _product_performance_report,

        "AI Executive Report": _ai_executive_report

    }

    renderers[category](bundle, dataset_id, dataset_name, generated_at)

    st.divider()

    st.subheader("📦 Export Full Workbook")

    st.caption(

        "One Excel file with Executive / Forecast / Inventory / "

        "Products sheets - everything in one download, regardless "

        "of which report category is selected above."

    )

    workbook_sheets = ReportService.combined_workbook_sheets(
        bundle,
        dataset_name
    )

    st.download_button(

        "⬇ Download Full Workbook (Excel)",

        export.to_excel_bytes(workbook_sheets),

        file_name=f"full_report_dataset_{dataset_id}.xlsx",

        mime=EXCEL_MIME,

        key="full_workbook"

    )

    page_footer()
