"""Tests for signal voting system."""

from __future__ import annotations

import pandas as pd

from bigshort.strategy.voting import signal_vote


def test_unanimous_buy():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    signals = {
        "technical": pd.Series([1, 1, 1, 1, 1], index=idx),
        "macro": pd.Series([1, 1, 1, 1, 1], index=idx),
    }
    result = signal_vote(signals, threshold=1.0)
    assert (result == 1).all()


def test_unanimous_sell():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    signals = {
        "technical": pd.Series([-1, -1, -1, -1, -1], index=idx),
        "macro": pd.Series([-1, -1, -1, -1, -1], index=idx),
    }
    result = signal_vote(signals, threshold=1.0)
    assert (result == -1).all()


def test_disagreement_goes_flat():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    signals = {
        "technical": pd.Series([1, 1, 1, 1, 1], index=idx),
        "macro": pd.Series([-1, -1, -1, -1, -1], index=idx),
    }
    result = signal_vote(signals, threshold=1.0)
    assert (result == 0).all()


def test_majority_threshold():
    idx = pd.date_range("2024-01-01", periods=3, freq="B")
    signals = {
        "a": pd.Series([1, 1, -1], index=idx),
        "b": pd.Series([1, -1, -1], index=idx),
        "c": pd.Series([1, 1, 1], index=idx),
    }
    result = signal_vote(signals, threshold=0.6)
    assert result.iloc[0] == 1   # 3/3 agree → avg=1.0 >= 0.6
    assert result.iloc[1] == 0   # 2 buy 1 sell → avg=0.33
    assert result.iloc[2] == 0   # 1 buy 2 sell → avg=-0.33
