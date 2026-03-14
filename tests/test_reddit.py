"""Tests for Reddit sentiment connector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from bigshort.sentiment.reddit import RedditSource, count_ticker_mentions


def test_count_ticker_mentions():
    posts = [
        {"title": "AAPL is going to moon! Also bullish on NVDA"},
        {"title": "Buy AAPL dip"},
        {"title": "Random post about nothing"},
    ]
    counts = count_ticker_mentions(posts, tickers=["AAPL", "NVDA", "TSLA"])
    assert counts["AAPL"] == 2
    assert counts["NVDA"] == 1
    assert counts["TSLA"] == 0


def test_count_ticker_mentions_empty():
    counts = count_ticker_mentions([], tickers=["AAPL"])
    assert counts["AAPL"] == 0


def test_fetch_returns_dataframe():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "children": [
                {"data": {"title": "AAPL to the moon", "created_utc": 1704200000}},
                {"data": {"title": "NVDA earnings play", "created_utc": 1704290000}},
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("bigshort.sentiment.reddit.requests.get", return_value=mock_response):
        src = RedditSource()
        df = src.fetch_mentions(tickers=["AAPL", "NVDA"], limit=25)

    assert "AAPL" in df.columns
    assert "NVDA" in df.columns
    assert df.index.name == "date"
