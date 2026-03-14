"""Backtest performance metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    """Annualized Sharpe ratio."""
    excess = returns - risk_free / TRADING_DAYS
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * np.sqrt(TRADING_DAYS))


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown from peak equity."""
    equity = (1 + returns).cumprod()
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return float(drawdown.min())


def backtest_report(returns: pd.Series) -> dict:
    """Generate a summary report for a return series."""
    total = float((1 + returns).prod() - 1)
    n_years = len(returns) / TRADING_DAYS
    ann_return = float((1 + total) ** (1 / max(n_years, 1e-9)) - 1)

    return {
        "sharpe_ratio": sharpe_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "total_return": total,
        "annualized_return": ann_return,
        "n_trading_days": len(returns),
    }
