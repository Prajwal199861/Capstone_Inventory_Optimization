"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : forecast_service.py

Description :
Milestone 3 - Phase 2B: Forecast Engine.

Generates demand forecasts from DemandService time series with
backtest-based model selection (MAPE/RMSE on a holdout window),
confidence bounds, and persistence of every run.
=============================================================================
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd

from config import EXPORTS_DIR

from database.session import SessionLocal

from models.forecast import Forecast
from models.forecast_point import ForecastPoint

from repositories.forecast_repository import ForecastRepository

from services.demand_service import DemandService

from utils.forecast_models import MODEL_REGISTRY, run_model


class ForecastService:

    AUTO_MODEL = "Auto"

    # Fraction of history held out for backtesting.
    HOLDOUT_FRACTION = 0.2

    MIN_HOLDOUT_PERIODS = 3

    # History must cover at least this many periods per granularity
    # (and always at least twice the requested horizon).
    MIN_HISTORY = {

        "Daily": 30,

        "Weekly": 12,

        "Monthly": 8

    }

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @staticmethod
    def generate_forecast(
            dataset_id: int,
            horizon_periods: int,
            granularity: str = "Monthly",
            measure: str = "Quantity",
            model: str = "Auto",
            created_by: int | None = None,
            product_id: str | None = None,
            store_id: str | None = None,
            category: str | None = None,
            scope: str | None = None
    ) -> dict:
        """
        Build the demand series, backtest all models, forecast with
        the chosen (or best) model, persist the run and return:

            {
                "forecast": DataFrame [Forecast, Lower, Upper],
                "history": DataFrame (the demand series),
                "model_name": str,
                "metrics": {model: {"mape": float|None, "rmse": float}},
                "backtest": {"index", "actual", "predictions"},
                "notes": [str],
                "forecast_id": int
            }
        """

        demand = DemandService.build_demand_series(

            dataset_id,

            granularity=granularity,

            measure=measure,

            product_id=product_id,

            store_id=store_id,

            category=category

        )

        history = demand["series"][measure]

        notes = list(demand["notes"])

        ForecastService._require_history(
            history,
            granularity,
            horizon_periods
        )

        backtest = ForecastService._backtest(
            history,
            granularity
        )

        metrics = backtest["metrics"]

        model_name = ForecastService._choose_model(
            model,
            metrics
        )

        values = run_model(
            model_name,
            history,
            horizon_periods,
            granularity
        )

        lower, upper = ForecastService._confidence_bounds(

            values,

            metrics[model_name]["rmse"]

        )

        index = ForecastService._future_index(

            history.index.max(),

            horizon_periods,

            granularity

        )

        forecast_frame = pd.DataFrame(

            {

                "Forecast": values,

                "Lower": lower,

                "Upper": upper

            },

            index=index

        )

        forecast_frame.index.name = "Period"

        if model == ForecastService.AUTO_MODEL:

            notes.append(

                f'Auto model selection chose "{model_name}" '

                f"(best MAPE on the holdout window)."

            )

        chosen_mape = metrics[model_name]["mape"]

        if chosen_mape is not None and chosen_mape > 50:

            notes.append(

                f"High backtest error (MAPE {chosen_mape:.0f}%): "

                f"demand is volatile at this granularity. A coarser "

                f"granularity (e.g. Weekly/Monthly) or a category "

                f"filter usually forecasts better."

            )

        forecast_id = ForecastService._persist(

            dataset_id=dataset_id,

            created_by=created_by or 0,

            measure=measure,

            granularity=granularity,

            horizon=horizon_periods,

            model_name=model_name,

            metrics=metrics[model_name],

            filters={

                "scope": scope,

                "product_id": product_id,

                "store_id": store_id,

                "category": category

            },

            points=[

                ForecastPoint(

                    period_date=period.to_pydatetime(),

                    value=float(row["Forecast"]),

                    lower=float(row["Lower"]),

                    upper=float(row["Upper"])

                )

                for period, row in forecast_frame.iterrows()

            ]

        )

        return {

            "forecast": forecast_frame,

            "history": demand["series"],

            "model_name": model_name,

            "metrics": metrics,

            "backtest": {

                "index": backtest["index"],

                "actual": backtest["actual"],

                "predictions": backtest["predictions"]

            },

            "notes": notes,

            "forecast_id": forecast_id

        }

    BATCH_SCOPE = "Batch"

    @staticmethod
    def generate_batch(
            dataset_id: int,
            horizon_periods: int,
            granularity: str = "Monthly",
            measure: str = "Quantity",
            created_by: int | None = None,
            progress_callback=None
    ) -> dict:
        """
        Forecast every product with sufficient history (Auto model
        per product) and persist ONE batch run whose points carry
        product_id. Phase 3 inventory optimization consumes this.

        Returns:

            {
                "summary": DataFrame [Product ID, Product Name,
                           Total Forecast, Model, MAPE (%), Status],
                "forecast_id": int | None,
                "forecasted": int,
                "skipped": int,
                "notes": [str]
            }

        Products with too little history are skipped with a reason;
        one bad product never fails the batch.
        """

        product_data = DemandService.build_product_series_map(

            dataset_id,

            granularity=granularity,

            measure=measure

        )

        summary_rows, points = ForecastService._batch_from_series_map(

            product_data["series_map"],

            product_data["names"],

            horizon_periods,

            granularity,

            progress_callback=progress_callback

        )

        forecast_id = None

        forecasted = sum(

            1 for row in summary_rows if row["Status"] == "Forecast"

        )

        if points:

            forecast_id = ForecastService._persist(

                dataset_id=dataset_id,

                created_by=created_by or 0,

                measure=measure,

                granularity=granularity,

                horizon=horizon_periods,

                model_name="Auto (per product)",

                metrics={},

                filters={"scope": ForecastService.BATCH_SCOPE},

                points=points

            )

        summary = pd.DataFrame(summary_rows)

        export_path = None

        if not summary.empty:

            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

            export_path = EXPORTS_DIR / (

                f"batch_forecast_dataset_{dataset_id}_"

                f"{datetime.now():%Y%m%d_%H%M%S}.csv"

            )

            summary.to_csv(export_path, index=False)

        return {

            "summary": summary,

            "forecast_id": forecast_id,

            "forecasted": forecasted,

            "skipped": len(summary_rows) - forecasted,

            "export_path": str(export_path) if export_path else None,

            "notes": product_data["notes"]

        }

    @staticmethod
    def _batch_from_series_map(
            series_map: dict,
            names: dict,
            horizon: int,
            granularity: str,
            progress_callback=None
    ):
        """
        Pure batch core: per product, guardrail-check, backtest,
        forecast with the best model. Returns (summary_rows, points).
        """

        summary_rows = []

        points = []

        total = len(series_map)

        for position, (product_id, series) in enumerate(
                series_map.items()
        ):

            if progress_callback:

                progress_callback(position + 1, total, product_id)

            name = names.get(product_id, product_id)

            try:

                ForecastService._require_history(
                    series,
                    granularity,
                    horizon
                )

                backtest = ForecastService._backtest(
                    series,
                    granularity
                )

                model_name = ForecastService._choose_model(
                    ForecastService.AUTO_MODEL,
                    backtest["metrics"]
                )

                values = run_model(
                    model_name,
                    series,
                    horizon,
                    granularity
                )

                lower, upper = ForecastService._confidence_bounds(

                    values,

                    backtest["metrics"][model_name]["rmse"]

                )

                index = ForecastService._future_index(

                    series.index.max(),

                    horizon,

                    granularity

                )

                points.extend(

                    ForecastPoint(

                        product_id=str(product_id),

                        period_date=period.to_pydatetime(),

                        value=float(value),

                        lower=float(low),

                        upper=float(high)

                    )

                    for period, value, low, high in zip(
                        index, values, lower, upper
                    )

                )

                mape = backtest["metrics"][model_name]["mape"]

                summary_rows.append({

                    "Product ID": product_id,

                    "Product Name": name,

                    "Total Forecast": round(float(values.sum()), 2),

                    "Model": model_name,

                    "MAPE (%)": (

                        round(mape, 1)

                        if mape is not None

                        else None

                    ),

                    "Status": "Forecast"

                })

            except ValueError as error:

                summary_rows.append({

                    "Product ID": product_id,

                    "Product Name": name,

                    "Total Forecast": None,

                    "Model": None,

                    "MAPE (%)": None,

                    "Status": f"Skipped: {error}"

                })

        return summary_rows, points

    @staticmethod
    def list_forecasts(
            dataset_id: int
    ):
        """Saved runs for a dataset, newest first."""

        session = SessionLocal()

        try:

            repository = ForecastRepository(session)

            return repository.get_by_dataset(dataset_id)

        finally:

            session.close()

    @staticmethod
    def count_forecasts() -> int:

        session = SessionLocal()

        try:

            return ForecastRepository(session).count_all()

        finally:

            session.close()

    # -----------------------------------------------------------------
    # Internal steps (pure, unit-testable)
    # -----------------------------------------------------------------

    @staticmethod
    def _require_history(
            history: pd.Series,
            granularity: str,
            horizon: int
    ):

        minimum = max(

            ForecastService.MIN_HISTORY.get(granularity, 8),

            2 * horizon

        )

        if len(history) < minimum:

            raise ValueError(

                f"Not enough history to forecast: {len(history)} "

                f"{granularity.lower()} periods available, at least "

                f"{minimum} required for a {horizon}-period horizon. "

                f"Try a shorter horizon or coarser granularity."

            )

    @staticmethod
    def _backtest(
            history: pd.Series,
            granularity: str
    ) -> dict:
        """
        Score every model on a holdout window.

        Returns:

            {
                "metrics": {model: {"mape", "rmse"}},
                "index": holdout period index,
                "actual": holdout actual values,
                "predictions": {model: predicted values}
            }

        Predictions are kept so the UI can show WHY the Auto
        selection chose its model.
        """

        holdout = max(

            ForecastService.MIN_HOLDOUT_PERIODS,

            int(len(history) * ForecastService.HOLDOUT_FRACTION)

        )

        train = history.iloc[:-holdout]

        actual = history.iloc[-holdout:].to_numpy(dtype=float)

        metrics = {}

        predictions = {}

        for model_name in MODEL_REGISTRY:

            predicted = run_model(

                model_name,

                train,

                holdout,

                granularity

            )

            predictions[model_name] = predicted

            metrics[model_name] = {

                "mape": ForecastService._mape(actual, predicted),

                "rmse": ForecastService._rmse(actual, predicted)

            }

        return {

            "metrics": metrics,

            "index": history.index[-holdout:],

            "actual": actual,

            "predictions": predictions

        }

    @staticmethod
    def _mape(
            actual: np.ndarray,
            predicted: np.ndarray
    ):
        """Mean absolute percentage error over nonzero actuals."""

        actual = np.asarray(actual, dtype=float)

        predicted = np.asarray(predicted, dtype=float)

        nonzero = actual != 0

        if not nonzero.any():

            return None

        return float(

            np.mean(

                np.abs(

                    (actual[nonzero] - predicted[nonzero])

                    / actual[nonzero]

                )

            ) * 100

        )

    @staticmethod
    def _rmse(
            actual: np.ndarray,
            predicted: np.ndarray
    ) -> float:

        actual = np.asarray(actual, dtype=float)

        predicted = np.asarray(predicted, dtype=float)

        return float(

            np.sqrt(np.mean((actual - predicted) ** 2))

        )

    @staticmethod
    def _choose_model(
            requested: str,
            metrics: dict
    ) -> str:
        """Auto picks best MAPE (RMSE as tie-break/fallback)."""

        if requested != ForecastService.AUTO_MODEL:

            if requested not in MODEL_REGISTRY:

                raise ValueError(
                    f"Unknown forecast model: {requested}"
                )

            return requested

        def sort_key(model_name):

            score = metrics[model_name]

            mape = score["mape"]

            return (

                mape if mape is not None else float("inf"),

                score["rmse"]

            )

        return min(metrics, key=sort_key)

    @staticmethod
    def _confidence_bounds(
            values: np.ndarray,
            rmse: float
    ):
        """
        ~95% bounds from the backtest error. Uncertainty compounds
        with distance, so the margin widens with the forecast step
        (std * sqrt(step)); demand floors at 0.
        """

        steps = np.arange(1, len(values) + 1, dtype=float)

        margin = 1.96 * rmse * np.sqrt(steps)

        lower = np.clip(values - margin, 0, None)

        upper = values + margin

        return lower, upper

    @staticmethod
    def _future_index(
            last_period,
            horizon: int,
            granularity: str
    ) -> pd.DatetimeIndex:

        frequency = DemandService.GRANULARITY_FREQUENCIES[granularity]

        offset = pd.tseries.frequencies.to_offset(frequency)

        return pd.date_range(

            start=last_period + offset,

            periods=horizon,

            freq=frequency

        )

    # -----------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------

    @staticmethod
    def _persist(
            dataset_id: int,
            created_by: int,
            measure: str,
            granularity: str,
            horizon: int,
            model_name: str,
            metrics: dict,
            filters: dict,
            points: list
    ) -> int:

        session = SessionLocal()

        try:

            repository = ForecastRepository(session)

            active_filters = {

                key: value

                for key, value in filters.items()

                if value is not None

            }

            forecast = Forecast(

                dataset_id=dataset_id,

                created_by=created_by,

                measure=measure,

                granularity=granularity,

                horizon=horizon,

                model_name=model_name,

                mape=metrics.get("mape"),

                rmse=metrics.get("rmse"),

                filters=json.dumps(active_filters)

            )

            repository.create(forecast)

            forecast.points = points

            session.commit()

            return forecast.id

        except Exception:

            session.rollback()

            raise

        finally:

            session.close()
