"""
=============================================================================
Dataset File Service
=============================================================================
"""

from pathlib import Path

from database.session import SessionLocal
from models.dataset import Dataset
from models.dataset_file import DatasetFile

from repositories.dataset_repository import DatasetRepository
from repositories.dataset_file_repository import DatasetFileRepository

from utils.dataset_utils import DatasetUtils
from utils.entity_detector import EntityDetector


class DatasetFileService:

    ALLOWED_EXTENSIONS = {
        ".csv",
        ".xlsx",
        ".xls"
    }

    @staticmethod
    def create_dataset_with_files(

            dataset_name: str,
            description: str,
            created_by: int,
            uploaded_files

    ):

        session = SessionLocal()

        folder = None

        try:

            dataset_repository = DatasetRepository(session)

            file_repository = DatasetFileRepository(session)

            existing = dataset_repository.get_by_name(
                dataset_name.strip()
            )

            if existing:

                raise ValueError(
                    f'Dataset "{dataset_name}" already exists.'
                )

            DatasetUtils.validate_dataset_name(
                dataset_name
            )

            dataset = Dataset(

                dataset_name=dataset_name.strip(),

                description=description,

                created_by=created_by

            )

            dataset_repository.create(dataset)

            folder = DatasetUtils.create_dataset_folder(
                dataset_name
            )

            dataset_files = []

            for uploaded_file in uploaded_files:

                extension = Path(
                    uploaded_file.name
                ).suffix.lower()

                if extension not in DatasetFileService.ALLOWED_EXTENSIONS:

                    raise ValueError(
                        f"{uploaded_file.name} is not a supported file."
                    )

                destination = folder / uploaded_file.name

                with open(destination, "wb") as f:

                    f.write(uploaded_file.getbuffer())

                dataset_file = DatasetFile(

                    dataset_id=dataset.id,

                    entity_type=EntityDetector.detect(
                        uploaded_file.name
                    ),

                    original_filename=uploaded_file.name,

                    stored_filename=uploaded_file.name,

                    relative_path=str(destination),

                    file_type=extension

                )

                dataset_files.append(dataset_file)

            file_repository.create_all(
                dataset_files
            )

            session.commit()

            return dataset

        except Exception:

            session.rollback()

            if folder and folder.exists():

                for file in folder.iterdir():

                    file.unlink()

                folder.rmdir()

            raise

        finally:

            session.close()