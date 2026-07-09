"""
=============================================================================
Dataset Validation Service
=============================================================================
"""

from database.session import SessionLocal

from repositories.dataset_repository import DatasetRepository
from repositories.dataset_file_repository import DatasetFileRepository
from repositories.column_mapping_repository import ColumnMappingRepository
from utils.metadata_engine import MetadataEngine

class DatasetValidationService:
    @staticmethod
    def validate_dataset(dataset_id: int):
        session = SessionLocal()
        try:
            dataset_repository = DatasetRepository(session)
            file_repository = DatasetFileRepository(session)
            mapping_repository = ColumnMappingRepository(session)
            dataset = dataset_repository.get_by_id(
                dataset_id
            )
            files = file_repository.get_by_dataset(
                dataset_id
            )
            dataset_ready = True
            for file in files:
                template = MetadataEngine.get_template(
                    file.entity_type
                )
                required_fields = template.get(
                    "required",
                    {}
                )
                mappings = mapping_repository.get_by_dataset_file(
                    file.id
                )
                mapped_fields = {
                    mapping.business_field
                    for mapping in mappings
                }
                missing = [
                    field
                    for field in required_fields
                    if field not in mapped_fields
                ]
                if missing:
                    dataset_ready = False
                    break
            if dataset_ready:
                dataset.status = "READY"
            else:
                dataset.status = "COLUMN_MAPPING_PENDING"
            session.commit()
            return dataset_ready
        finally:
            session.close()