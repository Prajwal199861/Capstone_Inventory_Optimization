"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : report_export.py

Description :
Milestone 4 - Phase 3: turns report data (already computed by
ReportService) and chart figures (already built by report_charts)
into downloadable bytes - CSV, Excel (single or multi-sheet) and PDF
(title, dataset, generated date, KPIs, charts, tables, summary). Pure
export mechanics only - no aggregation, no domain knowledge of what a
"report" contains.
=============================================================================
"""

from datetime import datetime
from io import BytesIO

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle
)


MAX_PDF_TABLE_ROWS = 100


def to_csv_bytes(
        table: pd.DataFrame
) -> bytes:

    if table is None:

        table = pd.DataFrame()

    return table.to_csv(index=False).encode("utf-8")


def to_excel_bytes(
        sheets: dict
) -> bytes:
    """sheets: {sheet_name: DataFrame}. Excel sheet names are capped
    at 31 characters by the format itself."""

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

        for name, table in sheets.items():

            (

                table if table is not None else pd.DataFrame()

            ).to_excel(

                writer,

                index=False,

                sheet_name=str(name)[:31]

            )

    return buffer.getvalue()


def build_pdf_bytes(
        title: str,
        dataset_name: str,
        generated_at: datetime,
        kpis: dict | None = None,
        charts: list | None = None,
        tables: list | None = None,
        summary_sections: dict | None = None
) -> bytes:
    """
    Assembles one PDF report.

    charts: [(chart_title, matplotlib.figure.Figure), ...]
    tables: [(table_title, DataFrame), ...] - each table is capped at
        MAX_PDF_TABLE_ROWS rows with a note pointing to the CSV/Excel
        export for the full data (a printable report is not the
        right medium for a raw dump of a large dataset).
    summary_sections: {section_label: text} - e.g. the AI Executive
        Report's five labeled sections.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        topMargin=0.6 * inch,

        bottomMargin=0.6 * inch,

        leftMargin=0.6 * inch,

        rightMargin=0.6 * inch

    )

    styles = getSampleStyleSheet()

    story = [

        Paragraph(title, styles["Title"]),

        Paragraph(f"Dataset: {dataset_name}", styles["Normal"]),

        Paragraph(
            f"Generated: {generated_at:%Y-%m-%d %H:%M}",
            styles["Normal"]
        ),

        Spacer(1, 14)

    ]

    if kpis:

        story.append(Paragraph("Key Metrics", styles["Heading2"]))

        story.append(_kpi_table(kpis))

        story.append(Spacer(1, 14))

    if charts:

        story.append(Paragraph("Charts", styles["Heading2"]))

        for chart_title, figure in charts:

            if chart_title:

                story.append(Paragraph(chart_title, styles["Heading3"]))

            story.append(_figure_to_image(figure))

            story.append(Spacer(1, 10))

    if tables:

        for table_title, table in tables:

            story.append(Paragraph(table_title, styles["Heading2"]))

            story.extend(_table_flowables(table, styles))

            story.append(Spacer(1, 14))

    if summary_sections:

        story.append(Paragraph("Summary", styles["Heading2"]))

        for label, text in summary_sections.items():

            story.append(Paragraph(label, styles["Heading3"]))

            story.append(
                Paragraph(text or "Not provided.", styles["BodyText"])
            )

            story.append(Spacer(1, 8))

    document.build(story)

    return buffer.getvalue()


def _kpi_table(
        kpis: dict
) -> Table:

    data = [[str(key), str(value)] for key, value in kpis.items()]

    table = Table(data, colWidths=[2.6 * inch, 3.2 * inch])

    table.setStyle(

        TableStyle([

            ("FONTSIZE", (0, 0), (-1, -1), 9),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            (
                "BACKGROUND",
                (0, 0), (0, -1),
                colors.HexColor("#EEEEEE")
            )

        ])

    )

    return table


def _figure_to_image(
        figure
) -> Image:

    buffer = BytesIO()

    figure.savefig(buffer, format="png", dpi=150, bbox_inches="tight")

    buffer.seek(0)

    width = 6.5 * inch

    aspect = figure.get_figheight() / figure.get_figwidth()

    return Image(buffer, width=width, height=width * aspect)


def _table_flowables(
        table: pd.DataFrame,
        styles,
        max_rows: int = MAX_PDF_TABLE_ROWS
) -> list:

    if table is None or table.empty:

        return [Paragraph("No data available.", styles["BodyText"])]

    display = table.head(max_rows)

    data = [list(display.columns)] + display.astype(str).values.tolist()

    rendered = Table(data, repeatRows=1)

    rendered.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0), (-1, 0),
                colors.HexColor("#1565C0")
            ),

            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("FONTSIZE", (0, 0), (-1, -1), 7),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            (
                "ROWBACKGROUNDS",
                (0, 1), (-1, -1),
                [colors.white, colors.HexColor("#F5F5F5")]
            )

        ])

    )

    flowables = [rendered]

    if len(table) > max_rows:

        flowables.append(Spacer(1, 6))

        flowables.append(

            Paragraph(

                f"Showing the first {max_rows} of {len(table)} rows - "

                f"see the CSV/Excel export for the full table.",

                styles["Italic"]

            )

        )

    return flowables
