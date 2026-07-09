"""
=============================================================================
Dataset Repository
=============================================================================
"""

from sqlalchemy.orm import Session

from models.dataset import Dataset


class DatasetRepository:

    def __init__(self, session: Session):

        self.session = session

    def create(
            self,
            dataset: Dataset
    ):

        self.session.add(dataset)

        self.session.flush()

        self.session.refresh(dataset)

        return dataset

    def get_by_name(
            self,
            dataset_name: str
    ):

        return (

            self.session

            .query(Dataset)

            .filter(
                Dataset.dataset_name.ilike(dataset_name)
            )

            .first()

        )

    def get_by_id(
            self,
            dataset_id: int
    ):

        return (

            self.session

            .query(Dataset)

            .filter(
                Dataset.id == dataset_id
            )

            .first()

        )

    def get_all(self):

        return (

            self.session

            .query(Dataset)

            .order_by(
                Dataset.created_at.desc()
            )

            .all()

        )

    def delete(
            self,
            dataset: Dataset
    ):

        self.session.delete(dataset)

    def get_by_user(
            self,
            user_id: int
    ):
        return (

            self.session

            .query(Dataset)

            .filter(
                Dataset.created_by == user_id
            )

            .order_by(
                Dataset.created_at.desc()
            )

            .all()

        )

    def get_by_id(
            self,
            dataset_id: int
    ):
        return (

            self.session

            .query(Dataset)

            .filter(

                Dataset.id == dataset_id

            )

            .first()

        )