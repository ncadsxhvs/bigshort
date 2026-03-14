"""Options straddle entry logic tied to low-vol regime detection."""

from __future__ import annotations

import pandas as pd


def detect_low_vol_entries(
    vol_series: pd.Series,
    threshold_percentile: int = 25,
) -> pd.Series:
    """Identify entry points where volatility is below a rolling percentile.

    Parameters
    ----------
    vol_series : pd.Series
        Realized or implied volatility series.
    threshold_percentile : int
        Percentile below which vol is considered "low".
    """
    threshold = vol_series.quantile(threshold_percentile / 100)
    return (vol_series <= threshold).rename("low_vol_entry")


def straddle_pnl(entry_price: float, exit_price: float, premium_paid: float) -> float:
    """Compute P&L of a straddle position.

    Straddle profits from large moves in either direction.
    P&L = |exit - entry| - premium_paid
    """
    return abs(exit_price - entry_price) - premium_paid
