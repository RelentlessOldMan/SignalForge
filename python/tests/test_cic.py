"""CIC decimator (ADR 0229)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_integrator_comb_structure() -> None:
    rng = np.random.default_rng(7)
    x = rng.integers(-100, 100, 200).astype(np.float64)
    r, n, m = 5, 4, 1
    s = x.copy()
    for _ in range(n):
        s = np.cumsum(s)
    s = s[::r]
    for _ in range(n):
        s = s - np.concatenate([np.zeros(m), s[:-m]])
    assert np.array_equal(sf.cic_decimate(x, r, n, delay=m), s)


def test_complex_is_real_and_imaginary_parts() -> None:
    rng = np.random.default_rng(8)
    a = rng.standard_normal(50)
    b = rng.standard_normal(50)
    y = sf.cic_decimate(a + 1j * b, 3, 3, delay=2)
    assert np.allclose(
        y, sf.cic_decimate(a, 3, 3, delay=2) + 1j * sf.cic_decimate(b, 3, 3, delay=2)
    )
