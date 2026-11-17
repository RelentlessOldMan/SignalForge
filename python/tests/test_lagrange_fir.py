"""Lagrange fractional-delay FIR (ADR 0225)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_delays_a_cubic_exactly() -> None:
    n = np.arange(40, dtype=np.float64)
    x = 0.01 * n**3 - 0.2 * n**2 + n - 3.0
    h = sf.lagrange_fir(1.7, 3)
    y = np.convolve(x, h)[3:40]
    t = n[3:40] - 1.7
    assert np.allclose(y, 0.01 * t**3 - 0.2 * t**2 + t - 3.0, atol=1e-9)


def test_flat_at_dc() -> None:
    assert abs(np.sum(sf.lagrange_fir(2.37, 6)) - 1.0) < 1e-13
