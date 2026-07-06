"""
=============================================================================
Dataset Utilities
=============================================================================
"""

import os
import re
from pathlib import Path

UPLOAD_ROOT = Path("uploads")


class DatasetUtils:

    @staticmethod
    def sanitize_dataset_name(dataset_name: str) -> str:
        """
        Convert dataset name into a safe folder name.
        """

        dataset_name = dataset_name.strip()

        dataset_name = re.sub(
            r'[<>:"/\\|?*]',
            "",
            dataset_name
        )

        dataset_name = dataset_name.replace(" ", "_")

        return dataset_name

    @staticmethod
    def get_dataset_folder(dataset_name: str) -> Path:

        folder_name = DatasetUtils.sanitize_dataset_name(
            dataset_name
        )

        return UPLOAD_ROOT / folder_name

    @staticmethod
    def create_dataset_folder(dataset_name: str) -> Path:

        folder = DatasetUtils.get_dataset_folder(
            dataset_name
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return folder

    @staticmethod
    def validate_dataset_name(dataset_name: str):

        if dataset_name is None:

            raise ValueError(
                "Dataset name is required."
            )

        dataset_name = dataset_name.strip()

        if dataset_name == "":

            raise ValueError(
                "Dataset name cannot be empty."
            )

        if len(dataset_name) < 3:

            raise ValueError(
                "Dataset name must contain at least 3 characters."
            )

        if len(dataset_name) > 100:

            raise ValueError(
                "Dataset name cannot exceed 100 characters."
            )