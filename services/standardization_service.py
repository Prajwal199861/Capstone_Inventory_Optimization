"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : standardization_service.py

Description :
Milestone 3 - Phase 1: Data Standardization Engine.

Transforms heterogeneous uploaded datasets into standardized
DataFrames keyed by entity type, using the column mappings
persisted during Milestone 2. Downstream modules (forecasting,
inventory optimization, reports, AI insights) must consume ONLY
this standardized representation and never read uploaded files
directly.
=============================================================================
"""

import pandas as pd

from database.session import SessionLocal

from repositories.dataset_repository import DatasetRepository
from repositories.dataset_file_repository import DatasetFileRepository
from repositories.column_mapping_repository import ColumnMappingRepository

from utils.dataframe_utils import DataFrameUtils
from utils.dataframe_cleaner import DataFrameCleaner


class StandardizationService:

    @staticmethod
    def load_standardized_dataset(
            dataset_id: int
    ) -> dict:
        """
        Standardize every mapped file of a dataset.

        Returns a dictionary keyed by entity type:

            {
                "Sales": DataFrame,
                "Products": DataFrame,
                ...
            }

        Entities without uploaded files or saved mappings are
        omitted. This is the contract consumed by the Phase 2
        Forecast Engine.
        """

        report = StandardizationService.load_with_report(
            dataset_id
        )

        return report["frames"]

    @staticmethod
    def load_with_report(
            dataset_id: int
    ) -> dict:
        """
        Same as load_standardized_dataset but also returns the
        cleaning warnings and skipped files for display in the UI.

        Returns:

            {
                "dataset_name": str,
                "frames": {entity_type: DataFrame},
                "warnings": [str],
                "skipped_files": [str]
            }
        """

        session = SessionLocal()

        try:

            dataset_repository = DatasetRepository(session)

            file_repository = DatasetFileRepository(session)

            mapping_repository = ColumnMappingRepository(session)

            dataset = dataset_repository.get_by_id(dataset_id)

            if dataset is None:

                raise ValueError(

                    f"Dataset {dataset_id} does not exist."

                )

            files = file_repository.get_by_dataset_id(dataset_id)

            frames: dict[str, pd.DataFrame] = {}

            warnings: list[str] = []

            skipped_files: list[str] = []

            for file in files:

                mappings = mapping_repository.get_by_dataset_file(
                    file.id
                )

                if not mappings:

                    skipped_files.append(file.original_filename)

                    warnings.append(

                        f"{file.original_filename}: no column mapping "

                        f"saved. File skipped."

                    )

                    continue

                frame, file_warnings = (

                    StandardizationService._standardize_file(

                        file,

                        mappings

                    )

                )

                warnings.extend(file_warnings)

                if frame is None:

                    skipped_files.append(file.original_filename)

                    continue

                entity = file.entity_type

                if entity in frames:

                    frames[entity] = pd.concat(

                        [frames[entity], frame],

                        ignore_index=True

                    )

                    warnings.append(

                        f"{entity}: multiple files combined into "

                        f"one standardized table."

                    )

                else:

                    frames[entity] = frame

            return {

                "dataset_name": dataset.dataset_name,

                "frames": frames,

                "warnings": warnings,

                "skipped_files": skipped_files

            }

        finally:

            session.close()

    @staticmethod
    def _standardize_file(
            file,
            mappings
    ):
        """
        Standardize one physical file:

        1. Read the uploaded file (never mutated).
        2. Rename dataset-specific columns to business fields.
        3. Keep only mapped business fields.
        4. Clean and normalize datatypes.

        Returns (DataFrame or None, warnings).
        """

        warnings = []

        try:

            dataframe = DataFrameUtils.read_dataframe(
                file.relative_path
            )

        except Exception as error:

            warnings.append(

                f"{file.original_filename}: could not be read "

                f"({error}). File skipped."

            )

            return None, warnings

        rename_map = {}

        for mapping in mappings:

            if mapping.mapped_column in dataframe.columns:

                rename_map[mapping.mapped_column] = (

                    mapping.business_field

                )

            else:

                warnings.append(

                    f'{file.original_filename}: mapped column '

                    f'"{mapping.mapped_column}" not found in file. '

                    f'Field "{mapping.business_field}" omitted.'

                )

        if not rename_map:

            warnings.append(

                f"{file.original_filename}: none of the mapped "

                f"columns exist in the file. File skipped."

            )

            return None, warnings

        dataframe = (

            dataframe[list(rename_map.keys())]

            .rename(columns=rename_map)

        )

        dataframe, clean_warnings = DataFrameCleaner.clean(

            dataframe,

            file.entity_type

        )

        warnings.extend(clean_warnings)

        return dataframe, warnings
