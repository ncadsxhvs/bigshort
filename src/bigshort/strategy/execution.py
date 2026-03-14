"""VWAP-style execution simulation with slippage."""

from __future__ import annotations

import pandas as pd

MIN_SLIPPAGE_BPS = 5


def apply_slippage(price: float, side: str, slippage_bps: int = MIN_SLIPPAGE_BPS) -> float:
    """Adjust price for slippage. Buy → higher, Sell → lower."""
    slip = price * slippage_bps / 10_000
    if side == "buy":
        return price + slip
    return price - slip


def simulate_execution(
    prices: pd.Series,
    signals: pd.Series,
    slippage_bps: int = MIN_SLIPPAGE_BPS,
) -> pd.Series:
    """Simulate execution of signals with slippage.

    Parameters
    ----------
    prices : pd.Series
        Asset price series.
    signals : pd.Series
        Position signals: 1 = long, -1 = short/sell, 0 = flat.
    slippage_bps : int
        Slippage in basis points applied on position changes.
    """
    returns = prices.pct_change().fillna(0.0)
    position = signals.shift(1).fillna(0)
    strategy_returns = position * returns

    changes = signals.diff().fillna(0).abs()
    slippage_cost = changes * slippage_bps / 10_000
    strategy_returns = strategy_returns - slippage_cost

    return strategy_returns
