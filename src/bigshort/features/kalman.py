"""1D Kalman filter for denoising price series."""

from __future__ import annotations

import numpy as np
import pandas as pd


def kalman_smooth(
    series: pd.Series,
    observation_noise: float = 1.0,
    process_noise: float = 0.01,
) -> pd.Series:
    """Apply a 1D Kalman filter to denoise a price series.

    Uses a constant-velocity state model: state = [price, velocity].

    Parameters
    ----------
    series : pd.Series
        Raw price series to smooth.
    observation_noise : float
        Measurement noise variance (R). Higher = more smoothing.
    process_noise : float
        Process noise variance (Q scaling). Higher = trusts observations more.
    """
    y = series.values.astype(float)
    n = len(y)

    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    Q = process_noise * np.eye(2)
    R = np.array([[observation_noise]])

    x = np.array([y[0], 0.0])
    P = np.eye(2)

    filtered = np.zeros(n)
    filtered[0] = y[0]

    for t in range(1, n):
        x_pred = F @ x
        P_pred = F @ P @ F.T + Q
        innovation = y[t] - H @ x_pred
        S = H @ P_pred @ H.T + R
        K = P_pred @ H.T @ np.linalg.inv(S)
        x = x_pred + (K @ innovation).flatten()
        P = (np.eye(2) - K @ H) @ P_pred
        filtered[t] = x[0]

    return pd.Series(filtered, index=series.index, name="kalman")
