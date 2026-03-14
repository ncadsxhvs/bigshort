"""Granger causality testing for lead/lag analysis."""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests


def granger_test(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 5,
    significance: float = 0.05,
) -> dict:
    """Test whether x Granger-causes y.

    Parameters
    ----------
    x : pd.Series
        Potential causal series.
    y : pd.Series
        Potential effect series.
    max_lag : int
        Maximum number of lags to test.
    significance : float
        P-value threshold for significance.

    Returns
    -------
    dict with keys: p_value, significant, best_lag
    """
    df = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
    results = grangercausalitytests(df, maxlag=max_lag, verbose=False)

    best_lag = 1
    best_p = 1.0
    for lag in range(1, max_lag + 1):
        p = results[lag][0]["ssr_ftest"][1]
        if p < best_p:
            best_p = p
            best_lag = lag

    return {
        "p_value": best_p,
        "significant": bool(best_p < significance),
        "best_lag": best_lag,
    }
