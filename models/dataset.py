"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : dataset.py

Description :
Represents a logical dataset uploaded into the system.
One dataset can contain multiple files such as:
- sales.csv
- products.csv
- customers.csv
- inventory.csv
=============================================================================
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Dataset(Base):

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dataset_name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    files = relationship(
        "DatasetFile",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return (
            f"<Dataset(id={self.id}, "
            f"name='{self.dataset_name}')>"
        )