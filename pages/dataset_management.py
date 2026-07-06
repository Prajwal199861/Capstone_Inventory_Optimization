"""
=============================================================================
Dataset Management Page
=============================================================================
"""

import streamlit as st

from components.header import page_header
from components.footer import page_footer
from services.dataset_service import DatasetService
from services.dataset_file_service import DatasetFileService


def dataset_management():

    page_header(
        "📂 Dataset Management",
        "Create a logical dataset and upload multiple files."
    )

    st.subheader("Create New Dataset")

    dataset_name = st.text_input(
        "Dataset Name"
    )

    description = st.text_area(
        "Description"
    )

    uploaded_files = st.file_uploader(
        "Upload CSV / Excel Files",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True
    )

    if uploaded_files:

        st.success(
            f"{len(uploaded_files)} file(s) selected."
        )

        st.write("### Uploaded Files")

        for file in uploaded_files:

            st.write(f"📄 {file.name}")

    if st.button(
        "Create Dataset",
        use_container_width=True
    ):

        if dataset_name.strip() == "":

            st.error(
                "Dataset name is required."
            )

            return

        try:

            DatasetFileService.create_dataset_with_files(

                dataset_name,

                description,

                st.session_state.user_id,

                uploaded_files

            )

            st.success(
                "Dataset created successfully."
            )

        except Exception as ex:

            st.error(str(ex))

    page_footer()