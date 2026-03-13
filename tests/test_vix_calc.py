"""Tests for custom VIX calculator module."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bigshort.features.vix_calc import realized_vol_index


def _trending_series(n: int = 100, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0005, 0.01, n)
    prices = 100 * np.exp(np.cumsum(returns))
    return pd.Series(prices, index=pd.date_range("2024-01-01", periods=n, freq="B"))


def test_output_length():
    assert len(realized_vol_index(_trending_series(), window=21)) == 100


def test_first_window_is_nan():
    vol = realized_vol_index(_trending_series(), window=21)
    assert vol.iloc[:21].isna().all()
    assert vol.iloc[21:].notna().all()


def test_annualized_scale():
    vol = realized_vol_index(_trending_series(n=300), window=21)
    median_vol = vol.dropna().median()
    assert 5.0 < median_vol < 40.0


def test_flat_series_near_zero_vol():
    flat = pd.Series([100.0] * 50, index=pd.date_range("2024-01-01", periods=50, freq="B"))
    vol = realized_vol_index(flat, window=10)
    assert (vol.dropna() == 0.0).all()


def test_higher_noise_higher_vol():
    rng = np.random.default_rng(99)
    idx = pd.date_range("2024-01-01", periods=200, freq="B")
    base = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.005, 200))), index=idx)
    wild = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 200))), index=idx)
    assert realized_vol_index(wild, 21).dropna().median() > realized_vol_index(base, 21).dropna().median()
