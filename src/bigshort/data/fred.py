"""FRED economic data connector."""

from __future__ import annotations

import os

import pandas as pd
from fredapi import Fred

from bigshort.data.base import DataSource

# Series we pull from FRED
DEFAULT_SERIES: dict[str, str] = {
    "treasury_10y": "DGS10",       # 10Y Treasury yield
    "real_yield_10y": "DFII10",    # 10Y TIPS real yield
    "cpi": "CPIAUCSL",             # CPI (monthly)
    "gdp": "GDP",                  # GDP (quarterly)
}


class FredSource(DataSource):
    """Pulls economic time series from FRED."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("FRED_API_KEY", "")
        if not key:
            raise RuntimeError(
                "FRED_API_KEY required. Set it in .env or pass api_key=."
            )
        self._fred = Fred(api_key=key)

    def fetch(self, ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
        """Fetch a FRED series by its ID (e.g. 'DGS10')."""
        kwargs: dict = {"observation_start": start}
        if end is not None:
            kwargs["observation_end"] = end
        series = self._fred.get_series(ticker, **kwargs)
        df = series.to_frame("close")
        df.index.name = "date"
        df = df.dropna()
        return df

    def fetch_all(
        self,
        start: str,
        end: str | None = None,
        series_map: dict[str, str] | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch all default FRED series, return keyed by friendly name."""
        mapping = series_map or DEFAULT_SERIES
        frames: dict[str, pd.DataFrame] = {}
        for key, fred_id in mapping.items():
            frames[key] = self.fetch(fred_id, start=start, end=end)
        return frames
