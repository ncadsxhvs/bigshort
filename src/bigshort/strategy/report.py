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


def trade_stats(returns: pd.Series, positions: pd.Series) -> dict:
    """Compute per-trade win rate and profit factor.

    A "trade" is a contiguous block of non-zero position.
    """
    trades: list[float] = []
    in_trade = False
    trade_return = 0.0

    for i in range(len(positions)):
        pos = positions.iloc[i]
        ret = returns.iloc[i]

        if pos != 0:
            if not in_trade:
                in_trade = True
                trade_return = 0.0
            trade_return += ret
        else:
            if in_trade:
                trades.append(trade_return)
                in_trade = False

    # Close final open trade
    if in_trade:
        trades.append(trade_return)

    if not trades:
        return {"n_trades": 0, "win_rate": 0.0, "profit_factor": 0.0,
                "avg_win": 0.0, "avg_loss": 0.0}

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    total_wins = sum(wins) if wins else 0.0
    total_losses = abs(sum(losses)) if losses else 0.0

    return {
        "n_trades": len(trades),
        "win_rate": len(wins) / len(trades),
        "profit_factor": total_wins / total_losses if total_losses > 0 else float("inf"),
        "avg_win": np.mean(wins) if wins else 0.0,
        "avg_loss": np.mean(losses) if losses else 0.0,
    }


def backtest_report(returns: pd.Series, positions: pd.Series | None = None) -> dict:
    """Generate a summary report for a return series."""
    total = float((1 + returns).prod() - 1)
    n_years = len(returns) / TRADING_DAYS
    ann_return = float((1 + total) ** (1 / max(n_years, 1e-9)) - 1)

    report = {
        "sharpe_ratio": sharpe_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "total_return": total,
        "annualized_return": ann_return,
        "n_trading_days": len(returns),
    }

    if positions is not None:
        report.update(trade_stats(returns, positions))

    return report
