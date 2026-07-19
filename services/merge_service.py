"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : merge_service.py

Description :
Milestone 3 - Phase 2A: combines standardized Sales frames that come
from split transactional files (e.g. orders.csv holding the date and
order_details.csv holding product and quantity) into one sales table
by joining on the shared "Order ID" business field.
=============================================================================
"""

import pandas as pd


class MergeService:

    @staticmethod
    def merge_sales_frames(
            sales_frames: list[pd.DataFrame]
    ):
        """
        Consolidate one or more standardized Sales frames into a single
        fact table with a usable "Transaction Date".

        Cases handled:
        - Single frame: returned unchanged.
        - Split files: the frame carrying "Quantity" (order lines) is
          left-joined with the frame carrying "Transaction Date"
          (order header) on "Order ID".
        - Multiple compatible fact frames: concatenated.

        Returns (sales_dataframe, notes).
        """

        notes = []

        if not sales_frames:

            raise ValueError(
                "No standardized Sales data available."
            )

        if len(sales_frames) == 1:

            return sales_frames[0], notes

        fact_frames = [
            frame
            for frame in sales_frames
            if "Quantity" in frame.columns
        ]

        header_frames = [
            frame
            for frame in sales_frames
            if "Quantity" not in frame.columns
            and "Transaction Date" in frame.columns
            and "Order ID" in frame.columns
        ]

        if not fact_frames:

            raise ValueError(
                "None of the Sales files contains a Quantity field."
            )

        facts = (

            pd.concat(fact_frames, ignore_index=True)

            if len(fact_frames) > 1

            else fact_frames[0]

        )

        needs_date = "Transaction Date" not in facts.columns

        if needs_date and header_frames and "Order ID" in facts.columns:

            header = pd.concat(
                header_frames,
                ignore_index=True
            )

            header_columns = [

                column

                for column in header.columns

                if column == "Order ID"

                or column not in facts.columns

            ]

            facts = facts.merge(

                header[header_columns].drop_duplicates(
                    subset=["Order ID"]
                ),

                on="Order ID",

                how="left"

            )

            notes.append(

                "Sales data was split across files: order lines were "

                "joined with order headers on 'Order ID'."

            )

        elif needs_date:

            raise ValueError(

                "Sales data has no 'Transaction Date' and no order "

                "header file to join it from. Map a date column first."

            )

        return facts, notes
