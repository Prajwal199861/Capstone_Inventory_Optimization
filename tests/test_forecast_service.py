"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : test_forecast_service.py

Description :
Unit tests for the Phase 2B forecast engine: model outputs on
synthetic series, backtest scoring, Auto model selection and the
minimum-history guardrail. Pure logic tests - no database access.

Run with either:
    python tests/test_forecast_service.py
    python -m pytest tests/
=============================================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from services.forecast_service import ForecastService
from utils.forecast_models import (
    MODEL_REGISTRY,
    holt_winters,
    moving_average,
    run_model,
    simple_exponential_smoothing,
)


def flat_series(n=60, value=100.0):

    index = pd.date_range("2025-01-01", periods=n, freq="D")

    return pd.Series(np.full(n, value), index=index)


def trending_series(n=60):

    index = pd.date_range("2025-01-01", periods=n, freq="D")

    return pd.Series(np.arange(n, dtype=float) * 2 + 10, index=index)


def seasonal_series(n=112):

    index = pd.date_range("2025-01-01", periods=n, freq="D")

    weekly = np.tile(
        [100, 100, 110, 120, 160, 220, 180],
        n // 7
    )

    return pd.Series(weekly.astype(float), index=index)


# ---------------------------------------------------------------------
# Model outputs
# ---------------------------------------------------------------------

def test_models_produce_horizon_length():

    for model_name in MODEL_REGISTRY:

        forecast = run_model(
            model_name, flat_series(), 30, "Daily"
        )

        assert len(forecast) == 30, model_name

        assert (forecast >= 0).all(), model_name


def test_moving_average_is_flat_mean():

    forecast = moving_average(flat_series(value=50.0), 10, window=7)

    assert np.allclose(forecast, 50.0)


def test_exponential_smoothing_tracks_level():

    forecast = simple_exponential_smoothing(
        flat_series(value=80.0), 5
    )

    assert np.allclose(forecast, 80.0, atol=1.0)


def test_holt_winters_follows_trend():

    forecast = holt_winters(trending_series(), 10, "Daily")

    # A trending series must keep growing beyond the last value (128)
    assert forecast[-1] > 128

    assert forecast[-1] > forecast[0]


def test_holt_winters_captures_weekly_seasonality():

    forecast = holt_winters(seasonal_series(), 7, "Daily")

    # Saturday (index 5 of the cycle) is the peak in the input;
    # the forecast week should peak well above its own minimum.
    assert forecast.max() - forecast.min() > 40


# ---------------------------------------------------------------------
# Accuracy metrics
# ---------------------------------------------------------------------

def test_mape_computation():

    actual = np.array([100.0, 200.0])

    predicted = np.array([110.0, 180.0])

    # (10/100 + 20/200) / 2 = 10%
    assert abs(ForecastService._mape(actual, predicted) - 10.0) < 1e-9


def test_mape_none_when_all_zero():

    assert ForecastService._mape(
        np.zeros(3), np.ones(3)
    ) is None


def test_rmse_computation():

    actual = np.array([1.0, 2.0, 3.0])

    predicted = np.array([1.0, 2.0, 6.0])

    assert abs(
        ForecastService._rmse(actual, predicted) - np.sqrt(3.0)
    ) < 1e-9


# ---------------------------------------------------------------------
# Backtesting and Auto selection
# ---------------------------------------------------------------------

def test_backtest_scores_every_model():

    backtest = ForecastService._backtest(seasonal_series(), "Daily")

    metrics = backtest["metrics"]

    assert set(metrics) == set(MODEL_REGISTRY)

    for score in metrics.values():

        assert score["rmse"] >= 0

    # Predictions for the comparison view cover the holdout window
    assert set(backtest["predictions"]) == set(MODEL_REGISTRY)

    assert len(backtest["index"]) == len(backtest["actual"])


def test_auto_picks_seasonal_model_on_seasonal_series():

    metrics = ForecastService._backtest(
        seasonal_series(), "Daily"
    )["metrics"]

    chosen = ForecastService._choose_model("Auto", metrics)

    # On a strongly weekly-seasonal series, Holt-Winters must beat
    # the flat models.
    assert chosen == "Holt-Winters"


def test_explicit_model_respected():

    metrics = ForecastService._backtest(
        flat_series(), "Daily"
    )["metrics"]

    assert ForecastService._choose_model(
        "Moving Average", metrics
    ) == "Moving Average"


def test_unknown_model_rejected():

    try:

        ForecastService._choose_model("Prophet", {})

        raise AssertionError("Expected ValueError")

    except ValueError as error:

        assert "Unknown" in str(error)


# ---------------------------------------------------------------------
# Guardrails and future index
# ---------------------------------------------------------------------

def test_short_history_rejected():

    try:

        ForecastService._require_history(
            flat_series(n=20), "Daily", 30
        )

        raise AssertionError("Expected ValueError")

    except ValueError as error:

        assert "Not enough history" in str(error)


def test_confidence_bounds_floor_at_zero():

    lower, upper = ForecastService._confidence_bounds(
        np.array([10.0, 100.0]), rmse=20.0
    )

    assert lower[0] == 0.0

    assert abs(upper[1] - 139.2) < 1e-9


def test_future_index_continues_after_history():

    index = ForecastService._future_index(
        pd.Timestamp("2025-03-31"), 3, "Monthly"
    )

    assert list(index) == [

        pd.Timestamp("2025-04-01"),

        pd.Timestamp("2025-05-01"),

        pd.Timestamp("2025-06-01")

    ]


# ---------------------------------------------------------------------
# Plain-python runner
# ---------------------------------------------------------------------

if __name__ == "__main__":

    failures = 0

    tests = [

        (name, function)

        for name, function in sorted(globals().items())

        if name.startswith("test_") and callable(function)

    ]

    for name, function in tests:

        try:

            function()

            print(f"PASS  {name}")

        except Exception as error:

            failures += 1

            print(f"FAIL  {name}: {error}")

    print(

        f"\n{len(tests) - failures}/{len(tests)} tests passed."

    )

    sys.exit(1 if failures else 0)
