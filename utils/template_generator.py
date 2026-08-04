"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : template_generator.py

Description :
Builds downloadable sample dataset templates (CSV/XLSX) for every
entity type MetadataEngine defines. Column headers are the exact
business field names (Required + Recommended, in that order) so a
filled-in template needs no renaming to map cleanly. Sample rows use
consistent IDs across entities (e.g. Product ID P001 appears in
Products, Sales and Inventory) so the templates can be combined into
one working demo dataset.
=============================================================================
"""

from io import BytesIO

import pandas as pd

from utils.metadata_engine import MetadataEngine


# Hand-authored example rows per entity - realistic values, not
# type-derived placeholders, and cross-referenced by ID across
# entities (Product ID, Store ID, Customer ID, Promotion ID).
SAMPLE_ROWS = {

    "Sales": [

        {
            "Transaction Date": "2026-01-05",
            "Product ID": "P001",
            "Quantity": 3,
            "Revenue": 44.97,
            "Store ID": "S001",
            "Customer ID": "C001",
            "Promotion ID": "",
            "Discount": 0
        },

        {
            "Transaction Date": "2026-01-06",
            "Product ID": "P002",
            "Quantity": 5,
            "Revenue": 64.95,
            "Store ID": "S002",
            "Customer ID": "C002",
            "Promotion ID": "PROMO01",
            "Discount": 5
        },

        {
            "Transaction Date": "2026-01-07",
            "Product ID": "P003",
            "Quantity": 2,
            "Revenue": 19.98,
            "Store ID": "S003",
            "Customer ID": "C001",
            "Promotion ID": "",
            "Discount": 0
        }

    ],

    "Products": [

        {
            "Product ID": "P001",
            "Product Name": "Wireless Mouse",
            "Category": "Electronics",
            "Sub Category": "Accessories",
            "Brand": "Acme",
            "Cost Price": 8.50,
            "Selling Price": 14.99
        },

        {
            "Product ID": "P002",
            "Product Name": "Cotton T-Shirt",
            "Category": "Apparel",
            "Sub Category": "Menswear",
            "Brand": "UrbanFit",
            "Cost Price": 4.20,
            "Selling Price": 12.99
        },

        {
            "Product ID": "P003",
            "Product Name": "Stainless Steel Bottle",
            "Category": "Home & Kitchen",
            "Sub Category": "Drinkware",
            "Brand": "HydroPro",
            "Cost Price": 3.10,
            "Selling Price": 9.99
        }

    ],

    "Stores": [

        {
            "Store ID": "S001",
            "Store Name": "Downtown Flagship",
            "City": "New York",
            "State": "NY",
            "Country": "USA",
            "Store Type": "Flagship"
        },

        {
            "Store ID": "S002",
            "Store Name": "Westside Mall",
            "City": "Los Angeles",
            "State": "CA",
            "Country": "USA",
            "Store Type": "Mall"
        },

        {
            "Store ID": "S003",
            "Store Name": "Riverside Outlet",
            "City": "Austin",
            "State": "TX",
            "Country": "USA",
            "Store Type": "Outlet"
        }

    ],

    "Inventory": [

        {
            "Product ID": "P001",
            "Current Stock": 120,
            "Store ID": "S001",
            "Warehouse": "WH-East",
            "Reorder Level": 40,
            "Safety Stock": 20,
            "Maximum Stock": 300
        },

        {
            "Product ID": "P002",
            "Current Stock": 60,
            "Store ID": "S002",
            "Warehouse": "WH-West",
            "Reorder Level": 30,
            "Safety Stock": 15,
            "Maximum Stock": 200
        },

        {
            "Product ID": "P003",
            "Current Stock": 15,
            "Store ID": "S003",
            "Warehouse": "WH-South",
            "Reorder Level": 25,
            "Safety Stock": 10,
            "Maximum Stock": 150
        }

    ],

    "Calendar": [

        {
            "Date": "2026-01-01",
            "Holiday": "Yes",
            "Weekend": "No",
            "Festival": "New Year"
        },

        {
            "Date": "2026-01-03",
            "Holiday": "No",
            "Weekend": "Yes",
            "Festival": ""
        },

        {
            "Date": "2026-01-26",
            "Holiday": "Yes",
            "Weekend": "No",
            "Festival": "Republic Day"
        }

    ],

    "Customers": [

        {
            "Customer ID": "C001",
            "Customer Name": "Alex Johnson",
            "Gender": "Male",
            "Age": 34
        },

        {
            "Customer ID": "C002",
            "Customer Name": "Priya Sharma",
            "Gender": "Female",
            "Age": 29
        }

    ],

    "Exchange Rates": [

        {
            "Date": "2026-01-01",
            "Currency": "USD",
            "Rate": 1.0
        },

        {
            "Date": "2026-01-01",
            "Currency": "EUR",
            "Rate": 0.92
        },

        {
            "Date": "2026-01-01",
            "Currency": "INR",
            "Rate": 83.10
        }

    ],

    "Promotions": [

        {
            "Promotion ID": "PROMO01",
            "Promotion Name": "New Year Sale",
            "Discount": 10,
            "Start Date": "2026-01-01",
            "End Date": "2026-01-15"
        },

        {
            "Promotion ID": "PROMO02",
            "Promotion Name": "Clearance",
            "Discount": 20,
            "Start Date": "2026-02-01",
            "End Date": "2026-02-10"
        }

    ]

}


class TemplateGenerator:

    @staticmethod
    def supported_entities() -> list[str]:
        """Entity types with a downloadable template, in a fixed,
        sensible order (master data before transactional data)."""

        order = [

            "Products",

            "Stores",

            "Sales",

            "Inventory",

            "Customers",

            "Calendar",

            "Promotions",

            "Exchange Rates"

        ]

        return [

            entity

            for entity in order

            if entity in MetadataEngine.ENTITY_TEMPLATES

        ]

    @staticmethod
    def field_columns(
            entity_type: str
    ) -> list[str]:
        """Required + Recommended business field names, in that
        order - the columns a template needs to be immediately
        usable without renaming during column mapping."""

        template = MetadataEngine.get_template(entity_type)

        return (

            list(template.get("required", {}).keys())

            + list(template.get("recommended", {}).keys())

        )

    @staticmethod
    def build_dataframe(
            entity_type: str
    ) -> pd.DataFrame:
        """Sample rows for one entity, limited to its Required +
        Recommended columns (Optional fields are left out of the
        template to keep it focused on what actually matters)."""

        columns = TemplateGenerator.field_columns(entity_type)

        rows = SAMPLE_ROWS.get(entity_type, [])

        if not rows:

            return pd.DataFrame(columns=columns)

        return pd.DataFrame(rows)[columns]

    @staticmethod
    def to_csv_bytes(
            entity_type: str
    ) -> bytes:

        return (

            TemplateGenerator

            .build_dataframe(entity_type)

            .to_csv(index=False)

            .encode("utf-8")

        )

    @staticmethod
    def to_xlsx_bytes(
            entity_type: str
    ) -> bytes:

        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

            TemplateGenerator.build_dataframe(entity_type).to_excel(

                writer,

                index=False,

                sheet_name=entity_type[:31]

            )

        return buffer.getvalue()
