"""Yahoo Finance data connector."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from bigshort.data.base import DataSource


class YFinanceSource(DataSource):
    """Pulls OHLCV data via the yfinance library."""

    def fetch(self, ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
        data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError(f"No data returned for {ticker}")
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        df = data.rename(columns=str.lower)
        df.index.name = "date"
        return df
