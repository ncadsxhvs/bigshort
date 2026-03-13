"""Main ETL pipeline — orchestrates data pulls, syncing, and caching."""

from __future__ import annotations

import pandas as pd

from bigshort import config
from bigshort.data.yfinance import YFinanceSource
from bigshort.etl.sync import align_to_trading_calendar
from bigshort.utils.cache import load_cache, save_cache


def run_daily_pull(
    start: str = config.DEFAULT_START,
    end: str | None = config.DEFAULT_END,
    use_cache: bool = True,
) -> dict[str, pd.DataFrame]:
    """Fetch all assets, align dates, and cache to parquet."""
    yf_src = YFinanceSource()

    assets = {
        "ndx": config.NDX_TICKER,
        "gold": config.GOLD_TICKER,
        "vix": config.VIX_TICKER,
        "gvz": config.GVZ_TICKER,
    }

    frames: dict[str, pd.DataFrame] = {}
    for key, ticker in assets.items():
        cached = load_cache(key) if use_cache else None
        if cached is not None:
            frames[key] = cached
        else:
            frames[key] = yf_src.fetch(ticker, start=start, end=end)

    aligned = align_to_trading_calendar(frames, reference_key="ndx")

    if use_cache:
        for key, df in aligned.items():
            save_cache(key, df)

    return aligned
