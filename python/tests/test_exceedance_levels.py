"""Exceedance levels (conventions: Exceedance levels; ADR 0169)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_it_matches_numpy_linear_quantiles() -> None:
    rng = np.random.default_rng(3)
    p = rng.exponential(size=101)
    n = np.array([0.0, 5.0, 10.0, 50.0, 90.0, 99.0, 100.0])
    assert np.allclose(sf.exceedance_levels(p, n), np.quantile(p, 1 - n / 100), rtol=1e-14)


def test_levels_fall_as_the_percent_rises() -> None:
    p = sf.time_weighting(np.random.default_rng(4).standard_normal(4000), 8000.0, 0.125)
    levels = sf.exceedance_levels(p, [10.0, 50.0, 90.0])
    assert levels[0] >= levels[1] >= levels[2]
