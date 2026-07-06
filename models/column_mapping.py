"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : column_mapping.py

Description :
Stores mapping between business fields and uploaded columns.
=============================================================================
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ColumnMapping(Base):

    __tablename__ = "column_mappings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dataset_file_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_files.id"),
        nullable=False
    )

    business_field: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    mapped_column: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    dataset_file = relationship(
        "DatasetFile",
        back_populates="mappings"
    )

    def __repr__(self):

        return (
            f"<ColumnMapping("
            f"{self.business_field}"
            f" -> "
            f"{self.mapped_column})>"
        )