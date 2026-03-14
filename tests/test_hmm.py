"""Tests for HMM regime detector."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bigshort.strategy.hmm import fit_regime_hmm, predict_regimes


def _two_regime_data(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    half = n // 2
    returns1 = rng.normal(0.001, 0.005, half)
    returns2 = rng.normal(-0.001, 0.02, n - half)
    returns = np.concatenate([returns1, returns2])
    vol = np.concatenate([np.full(half, 10.0), np.full(n - half, 25.0)])
    return pd.DataFrame({"returns": returns, "volatility": vol}, index=idx)


def test_fit_returns_model():
    data = _two_regime_data()
    model = fit_regime_hmm(data[["returns", "volatility"]], n_regimes=2)
    assert model is not None


def test_predict_regimes_length():
    data = _two_regime_data()
    model = fit_regime_hmm(data[["returns", "volatility"]], n_regimes=2)
    regimes = predict_regimes(model, data[["returns", "volatility"]])
    assert len(regimes) == len(data)


def test_predict_regimes_values():
    data = _two_regime_data()
    model = fit_regime_hmm(data[["returns", "volatility"]], n_regimes=2)
    regimes = predict_regimes(model, data[["returns", "volatility"]])
    assert set(regimes.unique()).issubset({0, 1})


def test_detects_regime_change():
    data = _two_regime_data()
    model = fit_regime_hmm(data[["returns", "volatility"]], n_regimes=2)
    regimes = predict_regimes(model, data[["returns", "volatility"]])
    first_half_mode = regimes.iloc[:200].mode().iloc[0]
    second_half_mode = regimes.iloc[300:].mode().iloc[0]
    assert first_half_mode != second_half_mode
