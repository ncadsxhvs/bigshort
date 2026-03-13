"""Custom VIX-style realized volatility index calculator."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def realized_vol_index(prices: pd.Series, window: int = 21) -> pd.Series:
    """Compute annualized rolling realized volatility (percentage).

    Parameters
    ----------
    prices : pd.Series
        Price series (must be positive).
    window : int
        Rolling window in trading days. Default 21 (~1 month).

    Returns
    -------
    pd.Series
        Annualized vol in percentage points (e.g., 16.0 = 16%).
    """
    log_returns = np.log(prices / prices.shift(1))
    rolling_std = log_returns.rolling(window).std()
    annualized = rolling_std * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    annualized.name = "realized_vol"
    return annualized
