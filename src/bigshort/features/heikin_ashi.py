"""Heikin-Ashi candle smoothing."""

from __future__ import annotations

import numpy as np
import pandas as pd


def heikin_ashi(ohlc: pd.DataFrame) -> pd.DataFrame:
    """Compute Heikin-Ashi candles from standard OHLC data.

    Parameters
    ----------
    ohlc : pd.DataFrame
        Must contain columns: open, high, low, close (lowercase).
    """
    o = ohlc["open"].values.astype(float)
    h = ohlc["high"].values.astype(float)
    lo = ohlc["low"].values.astype(float)
    c = ohlc["close"].values.astype(float)
    n = len(ohlc)

    ha_close = (o + h + lo + c) / 4.0

    ha_open = np.empty(n)
    ha_open[0] = (o[0] + c[0]) / 2.0
    for i in range(1, n):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0

    ha_high = np.maximum(h, np.maximum(ha_open, ha_close))
    ha_low = np.minimum(lo, np.minimum(ha_open, ha_close))

    return pd.DataFrame(
        {"ha_open": ha_open, "ha_high": ha_high, "ha_low": ha_low, "ha_close": ha_close},
        index=ohlc.index,
    )
