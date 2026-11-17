"""Savitzky-Golay (ADR 0233)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_reproduces_a_cubic_and_its_derivative() -> None:
    k = np.arange(40, dtype=np.float64)
    x = 0.01 * k**3 - 0.3 * k**2 + 2 * k - 1
    assert np.allclose(sf.savgol_filter(x, 9, 3), x, rtol=0, atol=1e-9)
    dx = 0.03 * k**2 - 0.6 * k + 2
    assert np.allclose(sf.savgol_filter(x, 9, 3, derivative=1), dx, rtol=0, atol=1e-9)


def test_matches_least_squares_fit() -> None:
    t = np.arange(-6, 7, dtype=np.float64)
    a = np.vander(t, 5, increasing=True)
    want = np.linalg.pinv(a)[0]
    assert np.allclose(sf.savgol_coefficients(13, 4), want, rtol=0, atol=1e-12)
