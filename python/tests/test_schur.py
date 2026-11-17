"""Schur recursion (ADR 0221)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_levinson() -> None:
    a = sf.reflection_to_lpc([0.6 + 0.2j, -0.4, 0.3j, 0.5, -0.2 - 0.1j])
    r = sf.lpc_to_autocorrelation(a, 0.7, 8)
    for order in range(1, 9):
        s = sf.schur(r, order)
        fit = sf.levinson(r, order)
        assert np.allclose(s.reflection, fit.reflection, atol=1e-12)
        assert abs(s.error - fit.error) < 1e-12


def test_real_stays_real() -> None:
    assert sf.schur([1.0, 0.5], 1).reflection.dtype == np.float64
