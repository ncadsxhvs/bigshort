"""Hidden Markov Model regime detector."""

from __future__ import annotations

import pandas as pd
from hmmlearn.hmm import GaussianHMM


def fit_regime_hmm(
    features: pd.DataFrame,
    n_regimes: int = 2,
    n_iter: int = 100,
    random_state: int = 42,
) -> GaussianHMM:
    """Fit a Gaussian HMM to feature data.

    Parameters
    ----------
    features : pd.DataFrame
        Feature matrix (e.g., returns, volatility columns).
    n_regimes : int
        Number of hidden states (2 = Risk-On / Safe-Haven).
    """
    model = GaussianHMM(
        n_components=n_regimes,
        covariance_type="full",
        n_iter=n_iter,
        random_state=random_state,
    )
    model.fit(features.values)
    return model


def predict_regimes(model: GaussianHMM, features: pd.DataFrame) -> pd.Series:
    """Predict regime labels for each observation."""
    labels = model.predict(features.values)
    return pd.Series(labels, index=features.index, name="regime")
