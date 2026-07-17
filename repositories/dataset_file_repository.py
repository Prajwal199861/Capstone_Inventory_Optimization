from sqlalchemy.orm import Session
from models.dataset_file import DatasetFile

class DatasetFileRepository:
    def __init__(self, session: Session):
        self.session = session
    def create(
            self,
            dataset_file: DatasetFile
    ):
        self.session.add(dataset_file)
        self.session.flush()
        self.session.refresh(dataset_file)
        return dataset_file
    def create_all(
            self,
            dataset_files: list[DatasetFile]
    ):
        self.session.add_all(dataset_files)
        self.session.flush()
        return dataset_files
    def get_by_dataset(
            self,
            dataset_id: int
    ):
        return (
            self.session
            .query(DatasetFile)
            .filter(
                DatasetFile.dataset_id == dataset_id
            )
            .all()
        )
    def delete(
            self,
            dataset_file: DatasetFile
    ):
        self.session.delete(dataset_file)
    def get_by_dataset_id(
            self,
            dataset_id: int
    ):
        return (
            self.session
            .query(DatasetFile)
            .filter(
                DatasetFile.dataset_id == dataset_id
            )
            .order_by(
                DatasetFile.entity_type
            )
            .all()
        )