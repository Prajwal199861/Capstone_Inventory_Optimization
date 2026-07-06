"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : dataset_file.py

Description :
Represents a physical CSV/Excel file belonging to a dataset.
=============================================================================
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class DatasetFile(Base):

    __tablename__ = "dataset_files"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    relative_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    dataset = relationship(
        "Dataset",
        back_populates="files"
    )

    mappings = relationship(
        "ColumnMapping",
        back_populates="dataset_file",
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return (
            f"<DatasetFile("
            f"id={self.id}, "
            f"entity='{self.entity_type}')>"
        )