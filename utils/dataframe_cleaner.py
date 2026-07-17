"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : dataframe_cleaner.py

Description :
Cleans a standardized DataFrame according to the Phase 1 data
cleaning rules:
- Trim whitespace.
- Remove duplicate rows where appropriate.
- Convert datatypes safely.
- Log warnings rather than silently dropping information.
- Never mutate original uploaded files.
=============================================================================
"""

import pandas as pd

from utils.datatype_converter import DatatypeConverter


class DataFrameCleaner:

    # Master-data entities where an exact duplicate row is
    # certainly redundant. Sales rows may legitimately repeat,
    # so duplicates there are reported but kept.
    DEDUPLICATE_ENTITIES = {

        "Products",

        "Stores",

        "Inventory",

        "Customers",

        "Promotions",

        "Suppliers",

        "Calendar"

    }

    @staticmethod
    def clean(
            dataframe: pd.DataFrame,
            entity_type: str
    ):
        """
        Clean a standardized DataFrame in a copy.

        Columns are expected to already carry business field
        names. Returns (clean_dataframe, warnings).
        """

        warnings = []

        dataframe = dataframe.copy()

        # -----------------------------------------------------
        # Drop rows where every mapped field is empty
        # -----------------------------------------------------

        empty_rows = int(dataframe.isna().all(axis=1).sum())

        if empty_rows:

            dataframe = dataframe.dropna(how="all")

            warnings.append(

                f"{entity_type}: removed {empty_rows} empty row(s)."

            )

        # -----------------------------------------------------
        # Datatype conversion (includes whitespace trimming)
        # -----------------------------------------------------

        for column in dataframe.columns:

            converted, column_warnings = DatatypeConverter.convert_column(

                dataframe[column],

                column

            )

            dataframe[column] = converted

            warnings.extend(

                f"{entity_type}: {warning}"

                for warning in column_warnings

            )

        # -----------------------------------------------------
        # Duplicate handling
        # -----------------------------------------------------

        duplicates = int(dataframe.duplicated().sum())

        if duplicates:

            if entity_type in DataFrameCleaner.DEDUPLICATE_ENTITIES:

                dataframe = dataframe.drop_duplicates()

                warnings.append(

                    f"{entity_type}: removed {duplicates} duplicate row(s)."

                )

            else:

                warnings.append(

                    f"{entity_type}: {duplicates} duplicate row(s) found "

                    f"and kept (may be legitimate repeat transactions)."

                )

        # -----------------------------------------------------
        # Missing value reporting
        # -----------------------------------------------------

        for column in dataframe.columns:

            missing = int(dataframe[column].isna().sum())

            if missing:

                warnings.append(

                    f'{entity_type}: "{column}" has {missing} '

                    f"missing value(s)."

                )

        dataframe = dataframe.reset_index(drop=True)

        return dataframe, warnings
