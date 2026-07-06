from database.session import SessionLocal
from models.dataset import Dataset
from repositories.dataset_repository import DatasetRepository


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