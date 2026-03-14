"""Tests for options straddle entry logic."""

from __future__ import annotations

import pandas as pd

from bigshort.strategy.straddle import detect_low_vol_entries, straddle_pnl


def test_detect_low_vol_entries():
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    vol = pd.Series([10.0] * 30 + [30.0] * 70, index=idx)
    entries = detect_low_vol_entries(vol, threshold_percentile=25)
    assert entries.iloc[:30].sum() > 0
    assert entries.iloc[70:].sum() == 0


def test_straddle_pnl_positive_on_big_move():
    assert straddle_pnl(entry_price=100.0, exit_price=115.0, premium_paid=5.0) > 0


def test_straddle_pnl_negative_on_small_move():
    assert straddle_pnl(entry_price=100.0, exit_price=102.0, premium_paid=5.0) < 0


def test_straddle_pnl_symmetric():
    pnl_up = straddle_pnl(entry_price=100.0, exit_price=110.0, premium_paid=3.0)
    pnl_down = straddle_pnl(entry_price=100.0, exit_price=90.0, premium_paid=3.0)
    assert pnl_up == pnl_down
