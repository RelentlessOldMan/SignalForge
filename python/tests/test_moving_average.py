"""Moving average (ADR 0241)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_convolution() -> None:
    x = np.random.default_rng(16).standard_normal(300)
    y = sf.moving_average(x, 25)
    want = np.convolve(x, np.ones(25) / 25)[:300]
    assert np.allclose(y, want, rtol=0, atol=1e-13)


def test_complex_stays_complex() -> None:
    y = sf.moving_average(np.array([1 + 1j, 3 - 1j]), 2)
    assert np.iscomplexobj(y)
    assert y[1] == 2 + 0j
