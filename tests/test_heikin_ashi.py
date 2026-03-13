"""Tests for Heikin-Ashi smoothing module."""

from __future__ import annotations

import pandas as pd
import pytest

from bigshort.features.heikin_ashi import heikin_ashi


def _sample_ohlc() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open":  [100.0, 102.0, 101.0, 103.0, 105.0],
            "high":  [103.0, 104.0, 103.0, 106.0, 107.0],
            "low":   [ 99.0, 100.0,  99.0, 101.0, 103.0],
            "close": [102.0, 101.0, 102.0, 105.0, 106.0],
        },
        index=pd.date_range("2024-01-01", periods=5, freq="B"),
    )


def test_output_has_correct_columns():
    ha = heikin_ashi(_sample_ohlc())
    assert set(ha.columns) == {"ha_open", "ha_high", "ha_low", "ha_close"}


def test_output_length_matches_input():
    ha = heikin_ashi(_sample_ohlc())
    assert len(ha) == 5


def test_first_bar_ha_close():
    ha = heikin_ashi(_sample_ohlc())
    assert ha["ha_close"].iloc[0] == pytest.approx((100 + 103 + 99 + 102) / 4)


def test_first_bar_ha_open():
    ha = heikin_ashi(_sample_ohlc())
    assert ha["ha_open"].iloc[0] == pytest.approx((100 + 102) / 2)


def test_ha_high_gte_ha_open_and_close():
    ha = heikin_ashi(_sample_ohlc())
    assert (ha["ha_high"] >= ha["ha_open"]).all()
    assert (ha["ha_high"] >= ha["ha_close"]).all()


def test_ha_low_lte_ha_open_and_close():
    ha = heikin_ashi(_sample_ohlc())
    assert (ha["ha_low"] <= ha["ha_open"]).all()
    assert (ha["ha_low"] <= ha["ha_close"]).all()
