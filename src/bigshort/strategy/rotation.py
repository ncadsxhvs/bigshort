"""NDX ↔ Gold rotation strategy based on HMM regimes."""

from __future__ import annotations

import pandas as pd

from bigshort.strategy.report import backtest_report


def rotation_signals(
    regimes: pd.Series,
    risk_on_regime: int = 0,
) -> pd.Series:
    """Generate rotation signals from regime labels.

    Risk-On regime → hold NDX (signal = 1)
    Safe-Haven regime → hold Gold (signal = -1)
    """
    return regimes.map(lambda r: 1 if r == risk_on_regime else -1).rename("signal")


def run_rotation_backtest(
    ndx_prices: pd.Series,
    gold_prices: pd.Series,
    regimes: pd.Series,
    risk_on_regime: int = 0,
    slippage_bps: int = 5,
) -> dict:
    """Run a long-only rotation backtest between NDX and Gold."""
    signals = rotation_signals(regimes, risk_on_regime)

    ndx_ret = ndx_prices.pct_change().fillna(0)
    gold_ret = gold_prices.pct_change().fillna(0)

    position = signals.shift(1).fillna(0)
    strategy_returns = position.where(position == 1, 0) * ndx_ret + \
                       (-position).where(position == -1, 0) * gold_ret

    changes = signals.diff().fillna(0).abs()
    slippage_cost = changes * slippage_bps / 10_000
    strategy_returns = strategy_returns - slippage_cost

    return {
        "returns": strategy_returns,
        "report": backtest_report(strategy_returns),
        "signals": signals,
    }
