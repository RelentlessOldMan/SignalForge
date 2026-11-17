"""Moving RMS (ADR 0239)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_full_windows_match_numpy() -> None:
    x = np.random.default_rng(14).standard_normal(300)
    y = sf.moving_rms(x, 25)
    for n in range(24, 300):
        assert abs(y[n] - np.sqrt(np.mean(x[n - 24 : n + 1] ** 2))) < 1e-14


def test_sine_rms() -> None:
    n = np.arange(1000)
    y = sf.moving_rms(2 * np.sin(2 * np.pi * n / 20), 100)
    assert np.allclose(y[99:], np.sqrt(2), rtol=0, atol=1e-12)
