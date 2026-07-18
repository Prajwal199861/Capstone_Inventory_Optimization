"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : demand_service.py

Description :
Milestone 3 - Phase 2A: builds forecast-ready demand time series from
standardized datasets. Consumes ONLY standardized business fields via
StandardizationService; never touches uploaded files or original
column names. The Phase 2B Forecast Engine consumes this service.
=============================================================================
"""

import pandas as pd

from database.session import SessionLocal

from repositories.dataset_repository import DatasetRepository

from services.standardization_service import StandardizationService
from services.merge_service import MergeService


class DemandService:

    GRANULARITY_FREQUENCIES = {

        "Daily": "D",

        "Weekly": "W-MON",

        "Monthly": "MS"

    }

    MEASURES = [

        "Quantity",

        "Revenue"

    ]

    # -----------------------------------------------------------------
    # Dataset access
    # -----------------------------------------------------------------

    @staticmethod
    def get_ready_datasets():
        """Datasets whose column mapping is complete (status READY)."""

        session = SessionLocal()

        try:

            repository = DatasetRepository(session)

            return repository.get_by_status("READY")

        finally:

            session.close()

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @staticmethod
    def build_demand_series(
            dataset_id: int,
            granularity: str = "Monthly",
            measure: str = "Quantity",
            product_id: str | None = None,
            store_id: str | None = None,
            category: str | None = None
    ) -> dict:
        """
        Build a continuous demand time series for a dataset.

        Returns:

            {
                "series": DataFrame indexed by period start date with
                          one column named after the measure,
                "notes": [str],
                "measure": str,
                "granularity": str
            }
        """

        if granularity not in DemandService.GRANULARITY_FREQUENCIES:

            raise ValueError(
                f"Unsupported granularity: {granularity}"
            )

        if measure not in DemandService.MEASURES:

            raise ValueError(
                f"Unsupported measure: {measure}"
            )

        sales, products, notes = DemandService._load_sales(
            dataset_id
        )

        sales, filter_notes = DemandService._apply_filters(

            sales,

            products,

            product_id=product_id,

            store_id=store_id,

            category=category

        )

        notes.extend(filter_notes)

        if measure == "Revenue":

            sales, revenue_notes = DemandService._ensure_revenue(
                sales,
                products
            )

            notes.extend(revenue_notes)

        series, aggregate_notes = DemandService._aggregate(

            sales,

            granularity,

            measure

        )

        notes.extend(aggregate_notes)

        return {

            "series": series,

            "notes": notes,

            "measure": measure,

            "granularity": granularity

        }

    @staticmethod
    def get_filter_options(
            dataset_id: int
    ) -> dict:
        """
        Filter values available in the dataset, for UI dropdowns:

            {
                "products": [(product_id, display_name)],
                "stores": [store_id],
                "categories": [category]
            }
        """

        sales, products, _ = DemandService._load_sales(dataset_id)

        options = {

            "products": [],

            "stores": [],

            "categories": []

        }

        if "Product ID" in sales.columns:

            product_ids = sorted(
                sales["Product ID"].dropna().unique().tolist()
            )

            names = {}

            if (

                    products is not None

                    and "Product ID" in products.columns

                    and "Product Name" in products.columns

            ):

                names = (

                    products

                    .dropna(subset=["Product ID"])

                    .drop_duplicates(subset=["Product ID"])

                    .set_index("Product ID")["Product Name"]

                    .to_dict()

                )

            options["products"] = [

                (product_id, names.get(product_id, product_id))

                for product_id in product_ids

            ]

        if "Store ID" in sales.columns:

            options["stores"] = sorted(
                sales["Store ID"].dropna().unique().tolist()
            )

        if (

                products is not None

                and "Category" in products.columns

        ):

            options["categories"] = sorted(
                products["Category"].dropna().unique().tolist()
            )

        return options

    # -----------------------------------------------------------------
    # Internal steps (pure, unit-testable)
    # -----------------------------------------------------------------

    @staticmethod
    def _load_sales(
            dataset_id: int
    ):
        """Load and consolidate Sales plus the Products master."""

        report = StandardizationService.load_frames_per_file(
            dataset_id
        )

        sales_frames = report["frames_per_file"].get("Sales", [])

        sales, notes = MergeService.merge_sales_frames(sales_frames)

        product_frames = report["frames_per_file"].get("Products", [])

        products = (

            pd.concat(product_frames, ignore_index=True)

            if product_frames

            else None

        )

        return sales, products, notes

    @staticmethod
    def _apply_filters(
            sales: pd.DataFrame,
            products: pd.DataFrame | None,
            product_id: str | None = None,
            store_id: str | None = None,
            category: str | None = None
    ):

        notes = []

        if product_id is not None:

            if "Product ID" not in sales.columns:

                raise ValueError(
                    "Sales data has no 'Product ID' field to filter on."
                )

            sales = sales[sales["Product ID"] == str(product_id)]

            notes.append(f"Filtered to product {product_id}.")

        if store_id is not None:

            if "Store ID" not in sales.columns:

                raise ValueError(
                    "Sales data has no 'Store ID' field to filter on."
                )

            sales = sales[sales["Store ID"] == str(store_id)]

            notes.append(f"Filtered to store {store_id}.")

        if category is not None:

            if (

                    products is None

                    or "Category" not in products.columns

                    or "Product ID" not in products.columns

            ):

                raise ValueError(
                    "Category filter needs Products data with "
                    "'Product ID' and 'Category' mapped."
                )

            category_products = products.loc[

                products["Category"] == category,

                "Product ID"

            ].dropna().unique()

            sales = sales[
                sales["Product ID"].isin(category_products)
            ]

            notes.append(f'Filtered to category "{category}".')

        return sales, notes

    @staticmethod
    def _ensure_revenue(
            sales: pd.DataFrame,
            products: pd.DataFrame | None
    ):
        """Derive Revenue from Products selling price when missing."""

        notes = []

        if (

                "Revenue" in sales.columns

                and sales["Revenue"].notna().any()

        ):

            return sales, notes

        if (

                products is None

                or "Selling Price" not in products.columns

                or "Product ID" not in products.columns

        ):

            raise ValueError(

                "Sales data has no 'Revenue' and it cannot be derived: "

                "Products with 'Selling Price' is not available. "

                "Use the Quantity measure instead."

            )

        if "Product ID" not in sales.columns:

            raise ValueError(

                "Cannot derive Revenue: Sales data has no 'Product ID' "

                "to join with Products."

            )

        prices = (

            products

            .dropna(subset=["Product ID"])

            .drop_duplicates(subset=["Product ID"])

            [["Product ID", "Selling Price"]]

        )

        sales = sales.merge(

            prices,

            on="Product ID",

            how="left",

            suffixes=("", "_product")

        )

        price_column = (

            "Selling Price"

            if "Selling Price_product" not in sales.columns

            else "Selling Price_product"

        )

        sales["Revenue"] = (

            pd.to_numeric(sales["Quantity"], errors="coerce")

            * pd.to_numeric(sales[price_column], errors="coerce")

        )

        notes.append(

            "Revenue derived from Products selling price "

            "(Quantity x Selling Price)."

        )

        unpriced = int(sales["Revenue"].isna().sum())

        if unpriced:

            notes.append(

                f"{unpriced} sales row(s) had no matching product "

                f"price and were excluded from revenue."

            )

        return sales, notes

    @staticmethod
    def _aggregate(
            sales: pd.DataFrame,
            granularity: str,
            measure: str
    ):
        """Aggregate to a continuous series (missing periods = 0)."""

        notes = []

        if "Transaction Date" not in sales.columns:

            raise ValueError(
                "Sales data has no 'Transaction Date' mapped."
            )

        if measure not in sales.columns:

            raise ValueError(
                f"Sales data has no '{measure}' field mapped."
            )

        dates = pd.to_datetime(
            sales["Transaction Date"],
            errors="coerce"
        )

        null_dates = int(dates.isna().sum())

        if null_dates:

            notes.append(

                f"{null_dates} sales row(s) with missing/invalid "

                f"dates were excluded."

            )

        values = pd.to_numeric(
            sales[measure],
            errors="coerce"
        ).fillna(0)

        valid = dates.notna()

        if not valid.any():

            raise ValueError(
                "No sales rows with a valid transaction date remain."
            )

        frequency = DemandService.GRANULARITY_FREQUENCIES[granularity]

        # Weekly needs explicit left labeling so the index carries the
        # period START (Monday); D and MS label period starts already.
        resample_options = (

            {"label": "left", "closed": "left"}

            if granularity == "Weekly"

            else {}

        )

        series = (

            pd.DataFrame({

                "period": dates[valid],

                measure: values[valid]

            })

            .set_index("period")

            .resample(frequency, **resample_options)

            [measure]

            .sum()

            .to_frame()

        )

        series.index.name = "Period"

        return series, notes
