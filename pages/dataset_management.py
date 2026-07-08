import streamlit as st
from components.header import page_header
from components.footer import page_footer
from services.dataset_service import DatasetService
from services.dataset_file_service import DatasetFileService

def dataset_management():
    status_icon = {
        "ACTIVE": "🟢",
        "READY": "🟢",
        "FILES_UPLOADED": "🟡",
        "ENTITY_MAPPING_PENDING": "🟠",
        "COLUMN_MAPPING_PENDING": "🔵"
    }
    page_header(
        "📂 Dataset Management",
        "Create a logical dataset and upload multiple files."
    )
    tab1, tab2 = st.tabs(
        [
            "📁 My Datasets",
            "➕ Create Dataset"
        ]
    )
    with tab1:
        datasets = DatasetService.get_user_datasets(
            st.session_state.user_id
        )
        if not datasets:
            st.info(
                "No datasets uploaded yet."
            )
        else:
            for dataset in datasets:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(
                            f"### 📁 {dataset.dataset_name}"
                        )
                        st.caption(
                            dataset.description
                            if dataset.description
                            else "No description"
                        )
                        st.write(
                            f"Status : "
                            f"{status_icon.get(dataset.status, '⚪')} "
                            f"{dataset.status}"
                        )
                    with c2:
                        if st.button(

                                "Open",

                                key=f"open_{dataset.id}",

                                use_container_width=True

                        ):
                            st.session_state.selected_dataset_id = dataset.id

                            st.session_state.current_page = "dataset_details"

                            st.rerun()
    with tab2:
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
            if not uploaded_files:
                st.error(
                    "Please upload at least one file."
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