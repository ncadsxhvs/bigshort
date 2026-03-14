"""Tests for sentiment feature engineering."""

from __future__ import annotations

import pandas as pd

from bigshort.sentiment.features import sentiment_delta


def test_sentiment_delta_weekly():
    idx = pd.date_range("2024-01-01", periods=21, freq="B")
    hawkishness = pd.Series(range(21), index=idx, dtype=float)
    delta = sentiment_delta(hawkishness, period=5)
    assert delta.iloc[:5].isna().all()
    assert delta.iloc[5] == 5.0
    assert delta.iloc[10] == 5.0


def test_sentiment_delta_default_period():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    hawkishness = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], index=idx, dtype=float)
    delta = sentiment_delta(hawkishness)
    assert delta.iloc[5] == 5.0
