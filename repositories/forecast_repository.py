"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : forecast_repository.py

Description :
CRUD access for saved forecast runs and their points.
=============================================================================
"""

from sqlalchemy.orm import Session, joinedload

from models.forecast import Forecast


class ForecastRepository:

    def __init__(self, session: Session):

        self.session = session

    def create(
            self,
            forecast: Forecast
    ):

        self.session.add(forecast)

        self.session.flush()

        self.session.refresh(forecast)

        return forecast

    def get_by_id(
            self,
            forecast_id: int
    ):

        return (

            self.session

            .query(Forecast)

            .options(joinedload(Forecast.points))

            .filter(
                Forecast.id == forecast_id
            )

            .first()

        )

    def get_by_dataset(
            self,
            dataset_id: int
    ):

        return (

            self.session

            .query(Forecast)

            .options(joinedload(Forecast.points))

            .filter(
                Forecast.dataset_id == dataset_id
            )

            .order_by(
                Forecast.created_at.desc()
            )

            .all()

        )

    def count_all(self):

        return (

            self.session

            .query(Forecast)

            .count()

        )

    def delete(
            self,
            forecast: Forecast
    ):

        self.session.delete(forecast)
