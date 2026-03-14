"""Tests for NewsAPI Fedspeak connector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from bigshort.sentiment.news import NewsSource, score_hawkishness


def test_newsource_requires_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="NEWSAPI_KEY"):
            NewsSource()


def test_score_hawkishness_hawk_keywords():
    articles = [
        {"title": "Fed signals rate hike ahead", "publishedAt": "2024-01-02T12:00:00Z"},
        {"title": "Inflation remains elevated and persistent", "publishedAt": "2024-01-02T14:00:00Z"},
    ]
    score = score_hawkishness(articles)
    assert score > 0


def test_score_hawkishness_dove_keywords():
    articles = [
        {"title": "Fed hints at rate cut soon", "publishedAt": "2024-01-02T12:00:00Z"},
        {"title": "Economy needs stimulus and easing", "publishedAt": "2024-01-02T14:00:00Z"},
    ]
    score = score_hawkishness(articles)
    assert score < 0


def test_score_hawkishness_neutral():
    articles = [
        {"title": "Weather forecast for Tuesday", "publishedAt": "2024-01-02T12:00:00Z"},
    ]
    score = score_hawkishness(articles)
    assert score == 0.0


def test_fetch_returns_dataframe():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "ok",
        "articles": [
            {"title": "Fed raises rates", "publishedAt": "2024-01-02T16:00:00Z"},
            {"title": "Markets rally on easing hopes", "publishedAt": "2024-01-03T10:00:00Z"},
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("bigshort.sentiment.news.requests.get", return_value=mock_response):
        src = NewsSource(api_key="test-key")
        df = src.fetch_fedspeak(start="2024-01-01", end="2024-01-05")

    assert "hawkishness" in df.columns
    assert df.index.name == "date"
