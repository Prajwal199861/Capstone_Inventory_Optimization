"""
=============================================================================
DataFrame Utilities
=============================================================================
"""

from pathlib import Path

import pandas as pd


class DataFrameUtils:

    @staticmethod
    def read_dataframe(file_path: str):

        extension = Path(file_path).suffix.lower()

        if extension == ".csv":

            return pd.read_csv(file_path)

        elif extension in [".xls", ".xlsx"]:

            return pd.read_excel(file_path)

        raise ValueError(
            f"Unsupported file type : {extension}"
        )