"""Tests for the YFinance data connector."""

from unittest.mock import patch

import pandas as pd
import pytest

from bigshort.data.yfinance import YFinanceSource


@pytest.fixture
def mock_ohlcv():
    idx = pd.date_range("2024-01-02", periods=5, freq="B")
    return pd.DataFrame(
        {"Close": [100, 101, 102, 103, 104], "Volume": [1e6] * 5},
        index=idx,
    )


def test_fetch_returns_dataframe(mock_ohlcv):
    with patch("bigshort.data.yfinance.yf.download", return_value=mock_ohlcv):
        src = YFinanceSource()
        df = src.fetch("^NDX", start="2024-01-02", end="2024-01-08")
    assert "close" in df.columns
    assert len(df) == 5


def test_fetch_raises_on_empty():
    with patch("bigshort.data.yfinance.yf.download", return_value=pd.DataFrame()):
        src = YFinanceSource()
        with pytest.raises(ValueError):
            src.fetch("BAD", start="2024-01-01")
