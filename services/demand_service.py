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

        sales, products, rates, notes = DemandService._load_sales(
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

            if (

                    "Revenue" in sales.columns

                    and sales["Revenue"].notna().any()

            ):

                # Native revenue may be in mixed local currencies.
                sales, currency_notes = (

                    DemandService._normalize_currency(

                        sales,

                        rates

                    )

                )

                notes.extend(currency_notes)

            else:

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
    def build_product_series_map(
            dataset_id: int,
            granularity: str = "Monthly",
            measure: str = "Quantity"
    ) -> dict:
        """
        One aligned demand series per product, loading the dataset
        only once (batch forecasting calls this instead of calling
        build_demand_series per product).

        Returns:

            {
                "series_map": {product_id: Series},
                "names": {product_id: product name},
                "notes": [str],
                "measure": str,
                "granularity": str
            }

        Every series spans the same global period range (gaps = 0)
        so downstream consumers can align products.
        """

        if granularity not in DemandService.GRANULARITY_FREQUENCIES:

            raise ValueError(
                f"Unsupported granularity: {granularity}"
            )

        sales, products, rates, notes = DemandService._load_sales(
            dataset_id
        )

        if "Product ID" not in sales.columns:

            raise ValueError(
                "Sales data has no 'Product ID' mapped."
            )

        if measure == "Revenue":

            if (

                    "Revenue" in sales.columns

                    and sales["Revenue"].notna().any()

            ):

                sales, currency_notes = (

                    DemandService._normalize_currency(

                        sales,

                        rates

                    )

                )

                notes.extend(currency_notes)

            else:

                sales, revenue_notes = DemandService._ensure_revenue(
                    sales,
                    products
                )

                notes.extend(revenue_notes)

        if "Transaction Date" not in sales.columns:

            raise ValueError(
                "Sales data has no 'Transaction Date' mapped."
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

        valid = dates.notna() & sales["Product ID"].notna()

        if not valid.any():

            raise ValueError(
                "No sales rows with a valid transaction date remain."
            )

        frequency = DemandService.GRANULARITY_FREQUENCIES[granularity]

        frame = pd.DataFrame({

            "period": dates[valid],

            "product": sales.loc[valid, "Product ID"],

            measure: pd.to_numeric(

                sales.loc[valid, measure],

                errors="coerce"

            ).fillna(0)

        })

        resample_options = (

            {"label": "left", "closed": "left"}

            if granularity == "Weekly"

            else {}

        )

        pivot = (

            frame

            .set_index("period")

            .groupby("product")[measure]

            .resample(frequency, **resample_options)

            .sum()

            .unstack(level="product")

        )

        # Align every product to the same continuous global range.
        full_range = pd.date_range(

            pivot.index.min(),

            pivot.index.max(),

            freq=frequency

        )

        pivot = pivot.reindex(full_range).fillna(0)

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

        series_map = {

            str(product): pivot[product]

            for product in pivot.columns

        }

        return {

            "series_map": series_map,

            "names": names,

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

        sales, products, _, _ = DemandService._load_sales(dataset_id)

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
        """Load and consolidate Sales, Products and Exchange Rates."""

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

        rate_frames = report["frames_per_file"].get(
            "Exchange Rates",
            []
        )

        rates = (

            pd.concat(rate_frames, ignore_index=True)

            if rate_frames

            else None

        )

        return sales, products, rates, notes

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
    def _normalize_currency(
            sales: pd.DataFrame,
            rates: pd.DataFrame | None
    ):
        """
        Convert native Revenue to the base currency using the mapped
        Exchange Rates entity (Date, Currency, Rate where Rate is
        units of local currency per one unit of base currency).

        Skips silently — returning sales unchanged — when the sales
        have no Currency field or the dataset has no usable rates.
        """

        notes = []

        required_rate_fields = {"Date", "Currency", "Rate"}

        if (

                "Currency" not in sales.columns

                or "Revenue" not in sales.columns

                or rates is None

                or not required_rate_fields.issubset(rates.columns)

        ):

            return sales, notes

        rates = rates.copy()

        rates["Date"] = pd.to_datetime(
            rates["Date"],
            errors="coerce"
        )

        rates["Rate"] = pd.to_numeric(
            rates["Rate"],
            errors="coerce"
        )

        rates = (

            rates

            .dropna(subset=["Date", "Currency", "Rate"])

            .sort_values("Date")

        )

        if rates.empty:

            return sales, notes

        # The base currency holds a constant rate of 1 (e.g. USD).
        base_candidates = [

            currency

            for currency, group in rates.groupby("Currency")

            if (group["Rate"] == 1).all()

        ]

        base_name = (

            base_candidates[0]

            if base_candidates

            else "base currency"

        )

        sales = sales.copy()

        sales["_row"] = range(len(sales))

        sales["_date"] = pd.to_datetime(
            sales["Transaction Date"],
            errors="coerce"
        )

        matchable = sales.dropna(subset=["_date"]).sort_values("_date")

        # Most recent rate on or before each sale date, per currency.
        matched = pd.merge_asof(

            matchable,

            rates.rename(columns={"Date": "_date"}),

            on="_date",

            left_by="Currency",

            right_by="Currency",

            direction="backward"

        )

        matched = matched.set_index("_row")

        rate = matched["Rate"]

        convertible = rate.notna() & (rate > 0)

        converted_revenue = matched.loc[convertible, "Revenue"] / (

            rate[convertible]

        )

        sales = sales.set_index("_row")

        sales.loc[converted_revenue.index, "Revenue"] = (

            converted_revenue

        )

        sales = (

            sales

            .reset_index(drop=True)

            .drop(columns=["_date"])

        )

        unconverted = int(len(matched) - int(convertible.sum()))

        notes.append(

            f"Revenue normalized to {base_name} using exchange rates."

        )

        if unconverted:

            notes.append(

                f"{unconverted} sales row(s) had no matching exchange "

                f"rate and kept their original amount."

            )

        return sales, notes

    @staticmethod
    def get_holiday_periods(
            dataset_id: int
    ) -> list:
        """
        Holiday/festival dates from the dataset's Calendar entity.
        Returns [] when the dataset has no mapped Calendar.
        """

        report = StandardizationService.load_frames_per_file(
            dataset_id
        )

        calendar_frames = report["frames_per_file"].get("Calendar", [])

        if not calendar_frames:

            return []

        calendar = pd.concat(calendar_frames, ignore_index=True)

        if "Date" not in calendar.columns:

            return []

        flags = pd.Series(False, index=calendar.index)

        for field in ("Holiday", "Festival"):

            if field in calendar.columns:

                flags |= calendar[field].map(
                    DemandService._is_truthy_flag
                )

        dates = pd.to_datetime(
            calendar.loc[flags, "Date"],
            errors="coerce"
        ).dropna()

        return sorted(dates.dt.normalize().unique().tolist())

    @staticmethod
    def _is_truthy_flag(value) -> bool:
        """'Yes'/'1'/'Diwali'/True count as flagged; blanks do not."""

        if value is None or (isinstance(value, float) and pd.isna(value)):

            return False

        text = str(value).strip().lower()

        return text not in ("", "0", "no", "false", "none", "nan")

    @staticmethod
    def holiday_effect_note(
            series: pd.Series,
            holiday_dates: list,
            threshold: float = 0.2
    ) -> str | None:
        """
        Compare mean demand on holiday vs non-holiday periods; a note
        is returned only when they differ by at least the threshold
        (default +/-20%). Meaningful for Daily series.
        """

        if not holiday_dates or series.empty:

            return None

        holidays = pd.DatetimeIndex(holiday_dates)

        on_holiday = series[series.index.isin(holidays)]

        off_holiday = series[~series.index.isin(holidays)]

        if on_holiday.empty or off_holiday.empty:

            return None

        baseline = float(off_holiday.mean())

        if baseline == 0:

            return None

        change = (float(on_holiday.mean()) - baseline) / baseline

        if abs(change) < threshold:

            return None

        direction = "higher" if change > 0 else "lower"

        return (

            f"Holiday effect: demand on holiday periods is "

            f"{abs(change) * 100:.0f}% {direction} than on regular "

            f"periods ({len(on_holiday)} holiday period(s) in range)."

        )

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
