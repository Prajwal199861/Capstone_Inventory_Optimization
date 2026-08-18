import shutil

from database.session import SessionLocal
from models.dataset import Dataset
from repositories.dataset_repository import DatasetRepository
from repositories.forecast_repository import ForecastRepository
from utils.dataset_utils import DatasetUtils


class DatasetService:

    @staticmethod
    def create_dataset(
            dataset_name: str,
            description: str,
            created_by: int
    ):

        session = SessionLocal()

        try:

            repository = DatasetRepository(session)

            existing = repository.get_by_name(
                dataset_name.strip()
            )

            if existing:
                raise ValueError(
                    f'Dataset "{dataset_name}" already exists.'
                )

            dataset = Dataset(
                dataset_name=dataset_name.strip(),
                description=description,
                created_by=created_by
            )

            repository.create(dataset)

            session.commit()

            return dataset

        except Exception:

            session.rollback()

            raise

        finally:

            session.close()

    @staticmethod
    def count_datasets() -> int:

        session = SessionLocal()

        try:

            return DatasetRepository(session).count_all()

        finally:

            session.close()

    @staticmethod
    def delete_dataset(
            dataset_id: int
    ):

        session = SessionLocal()

        try:

            dataset_repository = DatasetRepository(session)

            forecast_repository = ForecastRepository(session)

            dataset = dataset_repository.get_by_id(
                dataset_id
            )

            if not dataset:
                raise ValueError(
                    "Dataset not found."
                )

            for forecast in forecast_repository.get_by_dataset(
                    dataset_id
            ):
                forecast_repository.delete(forecast)

            folder = DatasetUtils.get_dataset_folder(
                dataset.dataset_name
            )

            dataset_repository.delete(dataset)

            session.commit()

            shutil.rmtree(
                folder,
                ignore_errors=True
            )

        except Exception:

            session.rollback()

            raise

        finally:

            session.close()

    @staticmethod
    def get_user_datasets(
            user_id: int
    ):

        session = SessionLocal()

        try:

            repository = DatasetRepository(session)

            return repository.get_by_user(
                user_id
            )

        finally:

            session.close()