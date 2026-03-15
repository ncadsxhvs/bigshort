"""MACD crossover signal generation and backtest."""

from __future__ import annotations

import pandas as pd

from bigshort.features.macd import macd
from bigshort.strategy.execution import simulate_execution
from bigshort.strategy.report import backtest_report


def macd_signals(macd_df: pd.DataFrame) -> pd.Series:
    """Generate signals from MACD crossover.

    Returns
    -------
    pd.Series
        1 when macd_line crosses above signal_line (long),
        -1 when macd_line crosses below signal_line (exit),
        0 otherwise.
    """
    above = macd_df["macd_line"] > macd_df["signal_line"]
    cross_up = above & ~above.shift(1, fill_value=False)
    cross_down = ~above & above.shift(1, fill_value=False)

    signal = pd.Series(0, index=macd_df.index, name="signal")
    signal[cross_up] = 1
    signal[cross_down] = -1
    return signal


def run_macd_backtest(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    slippage_bps: int = 5,
) -> dict:
    """Run a MACD crossover backtest.

    Returns dict with keys: returns, report, signals, macd.
    """
    macd_df = macd(prices, fast=fast, slow=slow, signal=signal)
    signals = macd_signals(macd_df)

    # Convert point signals to held positions: hold 1 after buy, 0 after sell
    position = pd.Series(0, index=signals.index, name="position")
    pos = 0
    for i, s in enumerate(signals):
        if s == 1:
            pos = 1
        elif s == -1:
            pos = 0
        position.iloc[i] = pos

    returns = simulate_execution(prices, position, slippage_bps=slippage_bps)

    return {
        "returns": returns,
        "report": backtest_report(returns),
        "signals": signals,
        "macd": macd_df,
    }
