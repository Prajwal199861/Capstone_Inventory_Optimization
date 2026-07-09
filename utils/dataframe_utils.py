import pandas as pd


class DataFrameUtils:

    @staticmethod
    def read_dataframe(file_path):

        if file_path.endswith(".csv"):

            encodings = [

                "utf-8",

                "utf-8-sig",

                "cp1252",

                "latin1"

            ]

            for encoding in encodings:

                try:

                    return pd.read_csv(

                        file_path,

                        encoding=encoding

                    )

                except UnicodeDecodeError:

                    continue

            raise ValueError(

                f"Unable to read CSV file: {file_path}"

            )

        elif file_path.endswith(".xlsx"):

            return pd.read_excel(file_path)

        elif file_path.endswith(".xls"):

            return pd.read_excel(file_path)

        else:

            raise ValueError(

                "Unsupported file format."

            )