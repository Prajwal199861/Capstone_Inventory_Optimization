"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : forecast.py

Description :
Represents one saved forecast run for a dataset (Milestone 3
Phase 2B). Points live in the forecast_points table.
=============================================================================
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Forecast(Base):

    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False
    )

    created_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    measure: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    granularity: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    horizon: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    model_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    mape: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    rmse: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    filters: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    points = relationship(
        "ForecastPoint",
        back_populates="forecast",
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return (
            f"<Forecast(id={self.id}, "
            f"dataset={self.dataset_id}, "
            f"model='{self.model_name}')>"
        )
