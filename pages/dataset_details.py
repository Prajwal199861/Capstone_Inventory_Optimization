"""
=============================================================================
Dataset Details
=============================================================================
"""

import streamlit as st

from services.preview_service import PreviewService
from components.header import page_header
from components.footer import page_footer
from services.column_mapping_service import ColumnMappingService
from services.dataset_file_service import DatasetFileService


def dataset_details():

    page_header(

        "📂 Dataset Details",

        "View uploaded dataset files."

    )

    dataset_id = st.session_state.selected_dataset_id

    files = DatasetFileService.get_dataset_files(
        dataset_id
    )

    if not files:

        st.warning(
            "No files found."
        )

        return

    st.subheader(
        "Uploaded Files"
    )

    for file in files:

        with st.container(border=True):

            c1, c2, c3 = st.columns(
                [4, 2, 1]
            )

            with c1:

                st.write(
                    f"📄 {file.original_filename}"
                )

            with c2:

                st.write(
                    file.entity_type
                )

            c3, c4 = st.columns(2)

            with c3:

                if st.button(
                        "Preview",
                        key=f"preview_{file.id}"
                ):
                    preview = PreviewService.get_preview(
                        file.relative_path
                    )

                    st.divider()

                    st.subheader(file.original_filename)

                    a, b = st.columns(2)

                    a.metric("Rows", preview["rows"])

                    b.metric("Columns", preview["columns"])

                    st.write("### Columns")

                    st.write(preview["column_names"])

                    st.dataframe(
                        preview["preview"],
                        use_container_width=True
                    )

            with c4:

                if st.button(
                        "Map Columns",
                        key=f"map_{file.id}"
                ):

                    mapping = PreviewService.get_column_mapping(

                        file.relative_path,

                        file.entity_type

                    )

                    st.divider()

                    st.subheader(
                        f"🗂 Column Mapping - {file.original_filename}"
                    )

                    template = mapping["mapping_template"]

                    selected_mapping = {}

                    section_icons = {
                        "required": "🔴",
                        "recommended": "🟡",
                        "optional": "⚪"
                    }

                    for section in ["required", "recommended", "optional"]:

                        if not template.get(section):
                            continue

                        st.markdown(
                            f"### {section_icons[section]} {section.capitalize()} Fields"
                        )

                        for business_field, suggested_column in template[section].items():

                            columns = ["-- Not Mapped --"] + mapping["columns"]

                            if suggested_column in mapping["columns"]:
                                default_index = columns.index(suggested_column)
                            else:
                                default_index = 0

                            selected_mapping[business_field] = st.selectbox(

                                business_field,

                                options=columns,

                                index=default_index,

                                key=f"{file.id}_{section}_{business_field}"

                            )

                        st.divider()

                    if st.button(

                            "💾 Save Mapping",

                            key=f"save_mapping_{file.id}",

                            use_container_width=True

                    ):

                        final_mapping = {}

                        for business_field, source_column in selected_mapping.items():

                            if source_column != "-- Not Mapped --":
                                final_mapping[business_field] = source_column

                        ColumnMappingService.save_mapping(

                            file.id,

                            final_mapping

                        )

                        st.success(

                            "Column mapping saved successfully."

                        )

    page_footer()