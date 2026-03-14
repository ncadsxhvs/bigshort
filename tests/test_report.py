"""Tests for backtest report metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bigshort.strategy.report import sharpe_ratio, max_drawdown, backtest_report


def _sample_returns(n: int = 252, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(
        rng.normal(0.0004, 0.01, n),
        index=pd.date_range("2024-01-01", periods=n, freq="B"),
    )


def test_sharpe_ratio_positive():
    # Use returns with clear positive drift
    returns = pd.Series([0.001] * 252)
    assert sharpe_ratio(returns) > 0


def test_sharpe_ratio_zero_vol():
    assert sharpe_ratio(pd.Series([0.0] * 100)) == 0.0


def test_max_drawdown_negative():
    assert max_drawdown(_sample_returns()) < 0


def test_max_drawdown_no_loss():
    assert max_drawdown(pd.Series([0.01] * 50)) == 0.0


def test_backtest_report_keys():
    report = backtest_report(_sample_returns())
    assert "sharpe_ratio" in report
    assert "max_drawdown" in report
    assert "total_return" in report
    assert "annualized_return" in report
