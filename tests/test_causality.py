"""Tests for Granger causality testing."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bigshort.features.causality import granger_test


def test_known_causal_relationship():
    """X causes Y with a 1-day lag → should detect causality."""
    rng = np.random.default_rng(42)
    n = 500
    x = rng.standard_normal(n).cumsum()
    y = np.zeros(n)
    y[0] = rng.standard_normal()
    for t in range(1, n):
        y[t] = 0.8 * x[t - 1] + 0.1 * rng.standard_normal()

    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    result = granger_test(pd.Series(x, index=idx), pd.Series(y, index=idx), max_lag=5)
    assert result["p_value"] < 0.05
    assert result["significant"] is True


def test_no_causal_relationship():
    """Two independent random walks → should NOT detect causality."""
    rng = np.random.default_rng(99)
    n = 500
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    x = pd.Series(rng.standard_normal(n).cumsum(), index=idx)
    y = pd.Series(rng.standard_normal(n).cumsum(), index=idx)
    result = granger_test(x, y, max_lag=5)
    assert result["p_value"] > 0.05
    assert result["significant"] is False


def test_returns_expected_keys():
    rng = np.random.default_rng(0)
    n = 200
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    x = pd.Series(rng.standard_normal(n), index=idx)
    y = pd.Series(rng.standard_normal(n), index=idx)
    result = granger_test(x, y, max_lag=3)
    assert "p_value" in result
    assert "significant" in result
    assert "best_lag" in result
