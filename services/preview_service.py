"""
=============================================================================
Preview Service
=============================================================================
"""

from utils.dataframe_utils import DataFrameUtils
from utils.metadata_engine import MetadataEngine

class PreviewService:

    @staticmethod
    def get_preview(file_path: str):

        dataframe = DataFrameUtils.read_dataframe(
            file_path
        )

        return {

            "rows": len(dataframe),

            "columns": len(dataframe.columns),

            "column_names": dataframe.columns.tolist(),

            "preview": dataframe.head(10)

        }

    @staticmethod
    def get_column_mapping(
            file_path: str,
            entity_type: str
    ):
        dataframe = DataFrameUtils.read_dataframe(
            file_path
        )

        suggestions = MetadataEngine.suggest_columns(

            entity_type,

            dataframe.columns.tolist()

        )

        return {

            "columns": dataframe.columns.tolist(),

            "mapping_template": suggestions

        }