"""Tests for Kalman filter denoising module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bigshort.features.kalman import kalman_smooth


def _make_noisy_sine(n: int = 200, noise_std: float = 0.5, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 4 * np.pi, n)
    clean = np.sin(t)
    noisy = clean + rng.normal(0, noise_std, n)
    return pd.Series(noisy, index=pd.date_range("2024-01-01", periods=n, freq="B"))


def test_output_shape_matches_input():
    raw = _make_noisy_sine()
    smoothed = kalman_smooth(raw)
    assert len(smoothed) == len(raw)
    assert smoothed.index.equals(raw.index)


def test_reduces_high_frequency_variance():
    raw = _make_noisy_sine()
    smoothed = kalman_smooth(raw)
    raw_hf_var = raw.diff().dropna().var()
    smooth_hf_var = smoothed.diff().dropna().var()
    assert smooth_hf_var < raw_hf_var * 0.5


def test_preserves_trend():
    raw = _make_noisy_sine()
    smoothed = kalman_smooth(raw)
    assert raw.corr(smoothed) > 0.9


def test_handles_flat_series():
    flat = pd.Series([100.0] * 50, index=pd.date_range("2024-01-01", periods=50, freq="B"))
    smoothed = kalman_smooth(flat)
    assert smoothed.std() < 1e-6


def test_custom_observation_noise():
    raw = _make_noisy_sine()
    smooth_default = kalman_smooth(raw)
    smooth_high_noise = kalman_smooth(raw, observation_noise=10.0)
    assert smooth_high_noise.diff().dropna().var() < smooth_default.diff().dropna().var()
