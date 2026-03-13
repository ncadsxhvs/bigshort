"""Tests for ETL sync and feature engineering logic."""

import numpy as np
import pandas as pd

from bigshort.etl.sync import align_to_trading_calendar
from bigshort.features.correlation import rolling_correlation, volatility_spread


def test_align_to_trading_calendar():
    dates_a = pd.date_range("2024-01-02", periods=5, freq="B")
    dates_b = pd.date_range("2024-01-02", periods=3, freq="B")

    frames = {
        "ndx": pd.DataFrame({"close": range(5)}, index=dates_a),
        "gold": pd.DataFrame({"close": [10, 11, 12]}, index=dates_b),
    }

    aligned = align_to_trading_calendar(frames, reference_key="ndx")
    assert len(aligned["gold"]) == 5
    assert aligned["gold"]["close"].iloc[-1] == 12


def test_rolling_correlation():
    n = 100
    rng = np.random.default_rng(42)
    a = pd.Series(rng.standard_normal(n).cumsum())
    b = pd.Series(rng.standard_normal(n).cumsum())
    corr = rolling_correlation(a, b, window=20)
    assert len(corr) == n
    assert corr.iloc[:19].isna().all()
    assert corr.iloc[19:].notna().all()


def test_volatility_spread():
    vix = pd.Series([20.0, 25.0, 30.0])
    gvz = pd.Series([10.0, 10.0, 15.0])
    vs = volatility_spread(vix, gvz)
    assert list(vs) == [2.0, 2.5, 2.0]
