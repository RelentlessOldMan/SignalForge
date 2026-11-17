"""Cross-correlation (conventions: Cross-correlation; ADR 0190)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_it_is_numpy_correlate_full() -> None:
    rng = np.random.default_rng(35)
    x = rng.standard_normal(9) + 1j * rng.standard_normal(9)
    y = rng.standard_normal(4) + 1j * rng.standard_normal(4)
    assert np.allclose(sf.cross_correlation(x, y), np.correlate(x, y, "full"))


def test_lags_from_zero_are_the_unscaled_autocorrelation() -> None:
    x = np.random.default_rng(36).standard_normal(12)
    r = sf.cross_correlation(x, x)
    assert np.allclose(r[11:], sf.autocorrelation(x, scaling="none"))
