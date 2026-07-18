"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : forecast_models.py

Description :
Milestone 3 - Phase 2B: isolated forecasting model functions.

Each model takes a historical demand series (pandas Series of numeric
values, one entry per period, as produced by DemandService) and a
horizon, and returns a numpy array of point forecasts of exactly
`horizon` values. Models are kept separate so each formula can be
tuned or replaced independently.
=============================================================================
"""

import warnings

import numpy as np
import pandas as pd


# Seasonal cycle length per granularity (used by Holt-Winters).
SEASONAL_PERIODS = {

    "Daily": 7,

    "Weekly": 52,

    "Monthly": 12

}


def moving_average(
        history: pd.Series,
        horizon: int,
        window: int = 7
) -> np.ndarray:
    """Flat forecast: mean of the last `window` periods."""

    window = min(window, len(history))

    level = float(history.tail(window).mean())

    return np.full(horizon, level)


def simple_exponential_smoothing(
        history: pd.Series,
        horizon: int
) -> np.ndarray:
    """Level-only exponential smoothing (statsmodels)."""

    from statsmodels.tsa.holtwinters import SimpleExpSmoothing

    with warnings.catch_warnings():

        warnings.simplefilter("ignore")

        fitted = SimpleExpSmoothing(
            history.to_numpy(dtype=float),
            initialization_method="estimated"
        ).fit()

    return np.asarray(fitted.forecast(horizon), dtype=float)


def holt_winters(
        history: pd.Series,
        horizon: int,
        granularity: str = "Monthly"
) -> np.ndarray:
    """
    Trend + seasonality when history allows it (two full seasonal
    cycles); falls back to trend-only, then to simple smoothing.
    """

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    values = history.to_numpy(dtype=float)

    seasonal_periods = SEASONAL_PERIODS.get(granularity, 12)

    with warnings.catch_warnings():

        warnings.simplefilter("ignore")

        if len(values) >= 2 * seasonal_periods:

            try:

                fitted = ExponentialSmoothing(

                    values,

                    trend="add",

                    seasonal="add",

                    seasonal_periods=seasonal_periods,

                    initialization_method="estimated"

                ).fit()

                return np.asarray(
                    fitted.forecast(horizon),
                    dtype=float
                )

            except Exception:

                pass

        try:

            fitted = ExponentialSmoothing(

                values,

                trend="add",

                initialization_method="estimated"

            ).fit()

            return np.asarray(
                fitted.forecast(horizon),
                dtype=float
            )

        except Exception:

            return simple_exponential_smoothing(history, horizon)


# Registry consumed by the ForecastService and the UI model selector.
MODEL_REGISTRY = {

    "Moving Average": moving_average,

    "Exponential Smoothing": simple_exponential_smoothing,

    "Holt-Winters": holt_winters

}


def run_model(
        model_name: str,
        history: pd.Series,
        horizon: int,
        granularity: str
) -> np.ndarray:
    """Dispatch a model by name; demand is clipped at zero."""

    if model_name not in MODEL_REGISTRY:

        raise ValueError(
            f"Unknown forecast model: {model_name}"
        )

    if model_name == "Holt-Winters":

        forecast = holt_winters(history, horizon, granularity)

    else:

        forecast = MODEL_REGISTRY[model_name](history, horizon)

    return np.clip(forecast, 0, None)
