import streamlit as st
from components.header import page_header
from components.footer import page_footer
from services.dataset_service import DatasetService
from services.dataset_file_service import DatasetFileService
from utils.metadata_engine import MetadataEngine
from utils.template_generator import TemplateGenerator


def _sample_templates_tab():

    st.subheader("Sample Dataset Templates")

    st.caption(
        "Download a starter file per dataset type with the exact "
        "column names the app recognizes (Required + Recommended "
        "fields) and a few example rows. IDs are cross-referenced "
        "across templates (e.g. Product ID P001 appears in Products, "
        "Sales and Inventory) so they can be combined into one "
        "working demo dataset."
    )

    file_format = st.radio(
        "File Format",
        ["CSV", "XLSX"],
        horizontal=True
    )

    for entity_type in TemplateGenerator.supported_entities():

        template = MetadataEngine.get_template(entity_type)

        with st.container(border=True):

            c1, c2 = st.columns([4, 1])

            with c1:

                st.markdown(f"**{entity_type}**")

                required = ", ".join(template.get("required", {}))

                recommended = ", ".join(
                    template.get("recommended", {})
                )

                st.caption(f"Required: {required}")

                if recommended:

                    st.caption(f"Recommended: {recommended}")

            with c2:

                if file_format == "CSV":

                    data = TemplateGenerator.to_csv_bytes(entity_type)

                    mime = "text/csv"

                    extension = "csv"

                else:

                    data = TemplateGenerator.to_xlsx_bytes(entity_type)

                    mime = (
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet"
                    )

                    extension = "xlsx"

                st.download_button(
                    "⬇ Download",
                    data,
                    file_name=(
                        f"{entity_type.lower().replace(' ', '_')}"
                        f"_template.{extension}"
                    ),
                    mime=mime,
                    key=f"template_{entity_type}",
                    use_container_width=True
                )


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
    tab1, tab2, tab3 = st.tabs(
        [
            "📁 My Datasets",
            "➕ Create Dataset",
            "📥 Sample Templates"
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
                    c1, c2, c3 = st.columns([4, 1, 1])
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
                    with c3:
                        if st.button(

                                "🗑 Delete",

                                key=f"delete_{dataset.id}",

                                use_container_width=True

                        ):
                            st.session_state[
                                f"confirm_delete_{dataset.id}"
                            ] = True

                    if st.session_state.get(
                            f"confirm_delete_{dataset.id}"
                    ):
                        st.warning(
                            f"Delete \"{dataset.dataset_name}\"? This "
                            f"permanently removes its files, column "
                            f"mappings, and any forecasts generated "
                            f"from it."
                        )
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button(

                                    "Confirm Delete",

                                    key=f"confirm_yes_{dataset.id}",

                                    use_container_width=True

                            ):
                                try:
                                    DatasetService.delete_dataset(
                                        dataset.id
                                    )
                                    del st.session_state[
                                        f"confirm_delete_{dataset.id}"
                                    ]
                                    st.success(
                                        "Dataset deleted."
                                    )
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))
                        with cc2:
                            if st.button(

                                    "Cancel",

                                    key=f"confirm_no_{dataset.id}",

                                    use_container_width=True

                            ):
                                del st.session_state[
                                    f"confirm_delete_{dataset.id}"
                                ]
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
    with tab3:
        _sample_templates_tab()
    page_footer()