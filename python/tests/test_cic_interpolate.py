"""CIC interpolator (ADR 0230)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_comb_integrator_structure() -> None:
    rng = np.random.default_rng(9)
    x = rng.integers(-100, 100, 60).astype(np.float64)
    r, n, m = 4, 3, 2
    s = x.copy()
    for _ in range(n):
        s = s - np.concatenate([np.zeros(m), s[:-m]])
    u = np.zeros(x.size * r)
    u[::r] = s
    for _ in range(n):
        u = np.cumsum(u)
    assert np.array_equal(sf.cic_interpolate(x, r, n, delay=m), u)


def test_is_zero_stuffed_convolution() -> None:
    x = np.array([0.5, -1.0, 2.0, 0.25])
    u = np.zeros(12)
    u[::3] = x
    assert np.allclose(sf.cic_interpolate(x, 3, 2), np.convolve(u, sf.cic_taps(3, 2))[:12])
