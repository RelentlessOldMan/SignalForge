"""Lattice analysis filter (conventions: Lattice analysis filter; ADR 0211)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_the_direct_form_filter() -> None:
    rng = np.random.default_rng(62)
    x = rng.standard_normal(200) + 1j * rng.standard_normal(200)
    k = 0.8 * (rng.random(8) - 0.5) + 0.3j * (rng.random(8) - 0.5)
    a = sf.reflection_to_lpc(k)
    assert np.allclose(sf.lattice_filter(x, k), np.convolve(x, a)[:200], atol=1e-12)


def test_burg_residual_has_the_fit_error() -> None:
    x = np.random.default_rng(63).standard_normal(4000)
    fit = sf.burg(x, 6)
    e = sf.lattice_filter(x, fit.reflection)[6:]
    assert abs(float(np.mean(e**2)) / fit.error - 1) < 0.05
