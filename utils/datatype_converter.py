"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : datatype_converter.py

Description :
Safe datatype conversion for standardized business fields.
Field types are declared per business field name so that
MetadataEngine remains the single source of entity definitions
while datatype rules live here.
=============================================================================
"""

import pandas as pd


class DatatypeConverter:

    # Business fields holding monetary or quantity values.
    NUMERIC_FIELDS = {

        "Quantity",

        "Revenue",

        "Discount",

        "Cost Price",

        "Selling Price",

        "Current Stock",

        "Reorder Level",

        "Safety Stock",

        "Maximum Stock",

        "Age",

        "Rate"

    }

    # If more than this fraction of non-null values fail conversion,
    # the original column is preserved and a warning is raised.
    MAX_FAILURE_RATIO = 0.5

    @staticmethod
    def is_date_field(business_field: str) -> bool:

        return (

            business_field == "Date"

            or business_field.endswith(" Date")

        )

    @staticmethod
    def is_numeric_field(business_field: str) -> bool:

        return business_field in DatatypeConverter.NUMERIC_FIELDS

    @staticmethod
    def is_identifier_field(business_field: str) -> bool:

        return business_field.endswith(" ID")

    @staticmethod
    def convert_column(
            series: pd.Series,
            business_field: str
    ):
        """
        Convert a single column to the datatype expected for the
        given business field.

        Returns (converted_series, warnings). If conversion fails
        for too many values, the original series is returned
        unchanged and a warning explains why.
        """

        warnings = []

        if DatatypeConverter.is_date_field(business_field):

            converted = pd.to_datetime(

                series,

                errors="coerce",

                format="mixed",

                dayfirst=False

            )

        elif DatatypeConverter.is_numeric_field(business_field):

            cleaned = series

            if cleaned.dtype == object:

                cleaned = (

                    cleaned

                    .astype(str)

                    .str.replace(r"[,\s]", "", regex=True)

                    .str.replace(r"[^0-9eE+\-.]", "", regex=True)

                    .replace("", None)

                )

            converted = pd.to_numeric(

                cleaned,

                errors="coerce"

            )

        elif DatatypeConverter.is_identifier_field(business_field):

            converted = series.astype("string").str.strip()

            return converted, warnings

        else:

            if series.dtype == object:

                series = series.astype("string").str.strip()

            return series, warnings

        # Count values that were lost during conversion.
        failed = int(

            (converted.isna() & series.notna()).sum()

        )

        non_null = int(series.notna().sum())

        if non_null and failed:

            ratio = failed / non_null

            if ratio > DatatypeConverter.MAX_FAILURE_RATIO:

                warnings.append(

                    f'"{business_field}": {failed} of {non_null} values '

                    f"could not be converted. Original values preserved."

                )

                return series, warnings

            warnings.append(

                f'"{business_field}": {failed} of {non_null} values '

                f"could not be converted and were set to missing."

            )

        return converted, warnings
