"""Signal voting system — trades fire only when modules align."""

from __future__ import annotations

import pandas as pd


def signal_vote(
    signals: dict[str, pd.Series],
    threshold: float = 1.0,
) -> pd.Series:
    """Combine multiple signal sources via voting.

    Parameters
    ----------
    signals : dict[str, pd.Series]
        Named signal series, each with values in {-1, 0, 1}.
    threshold : float
        Fraction of agreement required. 1.0 = unanimous.
        The average signal must exceed ±threshold to trigger.

    Returns
    -------
    pd.Series
        Combined signal: 1 (buy), -1 (sell), or 0 (flat/no consensus).
    """
    df = pd.DataFrame(signals)
    avg = df.mean(axis=1)
    result = pd.Series(0, index=avg.index, name="vote")
    result[avg >= threshold] = 1
    result[avg <= -threshold] = -1
    return result
