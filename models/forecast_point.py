"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : forecast_point.py

Description :
One forecast value for one future period, belonging to a Forecast
run (Milestone 3 Phase 2B).
=============================================================================
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ForecastPoint(Base):

    __tablename__ = "forecast_points"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("forecasts.id"),
        nullable=False
    )

    period_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    lower: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    upper: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    forecast = relationship(
        "Forecast",
        back_populates="points"
    )

    def __repr__(self):

        return (
            f"<ForecastPoint("
            f"forecast={self.forecast_id}, "
            f"period={self.period_date:%Y-%m-%d})>"
        )
