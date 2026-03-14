"""Sentiment feature engineering."""

from __future__ import annotations

import pandas as pd


def sentiment_delta(hawkishness: pd.Series, period: int = 5) -> pd.Series:
    """Week-over-week change in hawkishness score.

    Parameters
    ----------
    hawkishness : pd.Series
        Daily hawkishness scores.
    period : int
        Lookback period in trading days. Default 5 (one week).
    """
    return hawkishness.diff(period)
