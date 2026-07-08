"""
=============================================================================
Column Mapping Repository
=============================================================================
"""

from sqlalchemy.orm import Session

from models.column_mapping import ColumnMapping


class ColumnMappingRepository:

    def __init__(self, session: Session):

        self.session = session

    def save_all(
            self,
            mappings: list[ColumnMapping]
    ):

        self.session.add_all(mappings)

        self.session.flush()

        return mappings

    def get_by_dataset_file(
            self,
            dataset_file_id: int
    ):

        return (

            self.session

            .query(ColumnMapping)

            .filter(
                ColumnMapping.dataset_file_id == dataset_file_id
            )

            .all()

        )

    def delete_existing(
            self,
            dataset_file_id: int
    ):

        (

            self.session

            .query(ColumnMapping)

            .filter(
                ColumnMapping.dataset_file_id == dataset_file_id
            )

            .delete()

        )