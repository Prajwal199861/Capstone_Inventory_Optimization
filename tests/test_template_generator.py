"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_template_generator.py

Description :
Unit tests for the sample dataset template generator
(utils/template_generator.py). Verifies every supported entity's
template carries all its required fields, has consistent columns
across CSV/XLSX, and round-trips cleanly through pandas' own readers -
exactly what a user re-uploading the file would go through.

Run with either:
    python tests/test_template_generator.py
    python -m pytest tests/
=============================================================================
"""

import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from utils.metadata_engine import MetadataEngine
from utils.template_generator import TemplateGenerator


def test_supported_entities_are_all_known_to_metadata_engine():

    for entity in TemplateGenerator.supported_entities():

        assert entity in MetadataEngine.ENTITY_TEMPLATES


def test_field_columns_include_every_required_field():

    for entity in TemplateGenerator.supported_entities():

        required = MetadataEngine.get_template(entity)["required"]

        columns = TemplateGenerator.field_columns(entity)

        for field in required:

            assert field in columns, f"{entity} missing {field}"


def test_field_columns_put_required_before_recommended():

    template = MetadataEngine.get_template("Sales")

    columns = TemplateGenerator.field_columns("Sales")

    required_count = len(template["required"])

    assert columns[:required_count] == list(template["required"])


def test_build_dataframe_columns_match_field_columns():

    for entity in TemplateGenerator.supported_entities():

        df = TemplateGenerator.build_dataframe(entity)

        assert list(df.columns) == TemplateGenerator.field_columns(
            entity
        )


def test_build_dataframe_never_empty_for_supported_entities():

    for entity in TemplateGenerator.supported_entities():

        df = TemplateGenerator.build_dataframe(entity)

        assert len(df) > 0, f"{entity} template has no sample rows"


def test_csv_round_trips_with_same_columns():

    for entity in TemplateGenerator.supported_entities():

        csv_bytes = TemplateGenerator.to_csv_bytes(entity)

        parsed = pd.read_csv(BytesIO(csv_bytes))

        assert list(parsed.columns) == TemplateGenerator.field_columns(
            entity
        )

        assert len(parsed) == len(
            TemplateGenerator.build_dataframe(entity)
        )


def test_xlsx_round_trips_with_same_columns():

    for entity in TemplateGenerator.supported_entities():

        xlsx_bytes = TemplateGenerator.to_xlsx_bytes(entity)

        parsed = pd.read_excel(BytesIO(xlsx_bytes))

        assert list(parsed.columns) == TemplateGenerator.field_columns(
            entity
        )


def test_shared_ids_are_consistent_across_entity_templates():

    # A downloaded set of templates should combine into one working
    # demo dataset - Product IDs used in Sales/Inventory must exist
    # in the Products template, likewise Store ID and Promotion ID.
    products = TemplateGenerator.build_dataframe("Products")

    stores = TemplateGenerator.build_dataframe("Stores")

    sales = TemplateGenerator.build_dataframe("Sales")

    inventory = TemplateGenerator.build_dataframe("Inventory")

    promotions = TemplateGenerator.build_dataframe("Promotions")

    known_products = set(products["Product ID"])

    known_stores = set(stores["Store ID"])

    known_promotions = set(promotions["Promotion ID"])

    assert set(sales["Product ID"]).issubset(known_products)

    assert set(sales["Store ID"]).issubset(known_stores)

    assert set(inventory["Product ID"]).issubset(known_products)

    assert set(inventory["Store ID"]).issubset(known_stores)

    used_promotions = set(sales["Promotion ID"]) - {""}

    assert used_promotions.issubset(known_promotions)


# ---------------------------------------------------------------------
# Plain-python runner
# ---------------------------------------------------------------------

if __name__ == "__main__":

    failures = 0

    tests = [

        (name, function)

        for name, function in sorted(globals().items())

        if name.startswith("test_") and callable(function)

    ]

    for name, function in tests:

        try:

            function()

            print(f"PASS  {name}")

        except Exception as error:

            failures += 1

            print(f"FAIL  {name}: {error}")

    print(

        f"\n{len(tests) - failures}/{len(tests)} tests passed."

    )

    sys.exit(1 if failures else 0)
