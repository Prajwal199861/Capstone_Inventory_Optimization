"""
=============================================================================
Dataset Preview
=============================================================================
"""

import streamlit as st

from services.preview_service import PreviewService


def dataset_preview(file_record):

    st.subheader("Dataset Preview")

    preview = PreviewService.get_preview(

        file_record.relative_path

    )

    c1, c2 = st.columns(2)

    with c1:

        st.metric(

            "Rows",

            preview["rows"]

        )

    with c2:

        st.metric(

            "Columns",

            preview["columns"]

        )

    st.write("Columns")

    st.write(

        preview["column_names"]

    )

    st.dataframe(

        preview["preview"],

        use_container_width=True

    )