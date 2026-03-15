"""MACD oscillator indicator."""

from __future__ import annotations

import pandas as pd


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Compute MACD oscillator from a closing price series.

    Parameters
    ----------
    close : pd.Series
        Closing prices.
    fast : int
        Fast EMA period.
    slow : int
        Slow EMA period.
    signal : int
        Signal line EMA period.
    """
    fast_ema = close.ewm(span=fast, adjust=False).mean()
    slow_ema = close.ewm(span=slow, adjust=False).mean()

    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame(
        {"macd_line": macd_line, "signal_line": signal_line, "histogram": histogram},
        index=close.index,
    )
