"""Tests for execution simulation."""

from __future__ import annotations

import pandas as pd
import pytest

from bigshort.strategy.execution import apply_slippage, simulate_execution


def test_apply_slippage_buy():
    assert apply_slippage(100.0, side="buy", slippage_bps=5) == pytest.approx(100.05)


def test_apply_slippage_sell():
    assert apply_slippage(100.0, side="sell", slippage_bps=5) == pytest.approx(99.95)


def test_simulate_execution_reduces_returns():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    prices = pd.Series([100, 105, 103, 108, 110], index=idx, dtype=float)
    signals = pd.Series([1, 1, -1, 1, 1], index=idx)
    returns_clean = simulate_execution(prices, signals, slippage_bps=0)
    returns_slip = simulate_execution(prices, signals, slippage_bps=5)
    assert (1 + returns_slip).prod() < (1 + returns_clean).prod()


def test_simulate_execution_length():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    prices = pd.Series(range(100, 110), index=idx, dtype=float)
    signals = pd.Series([1] * 10, index=idx)
    assert len(simulate_execution(prices, signals, slippage_bps=5)) == 10
