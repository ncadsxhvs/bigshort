"""Rolling correlation and volatility spread features."""

from __future__ import annotations

import pandas as pd

from bigshort.config import CORRELATION_WINDOW


def rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = CORRELATION_WINDOW,
) -> pd.Series:
    """Compute rolling Pearson correlation between two series."""
    return series_a.rolling(window).corr(series_b)


def volatility_spread(vix: pd.Series, gvz: pd.Series) -> pd.Series:
    """VIX / GVZ ratio — equity-vs-gold implied-vol spread."""
    return vix / gvz
