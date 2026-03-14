"""Tests for NDX/Gold rotation backtest."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bigshort.strategy.rotation import rotation_signals, run_rotation_backtest


def _sample_data(n: int = 100, seed: int = 42):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    ndx = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.001, 0.01, n))), index=idx)
    gold = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0005, 0.008, n))), index=idx)
    regimes = pd.Series([0] * 50 + [1] * 50, index=idx)
    return ndx, gold, regimes


def test_rotation_signals_values():
    ndx, gold, regimes = _sample_data()
    signals = rotation_signals(regimes, risk_on_regime=0)
    assert (signals.iloc[:50] == 1).all()
    assert (signals.iloc[50:] == -1).all()


def test_run_rotation_backtest_returns_dict():
    ndx, gold, regimes = _sample_data()
    result = run_rotation_backtest(ndx, gold, regimes, risk_on_regime=0)
    assert "returns" in result
    assert "report" in result
    assert len(result["returns"]) == len(ndx)


def test_rotation_backtest_has_metrics():
    ndx, gold, regimes = _sample_data()
    result = run_rotation_backtest(ndx, gold, regimes, risk_on_regime=0)
    assert "sharpe_ratio" in result["report"]
    assert "max_drawdown" in result["report"]
