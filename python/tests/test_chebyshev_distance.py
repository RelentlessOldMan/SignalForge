"""The Chebyshev distance (ADR 0420)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_numpy_infinity_norm() -> None:
    rng = np.random.default_rng(175)
    x, y = rng.normal(size=20), rng.normal(size=20)
    assert sf.chebyshev_distance(x, y) == np.linalg.norm(x - y, ord=np.inf)


def test_is_the_limit_of_the_minkowski_distance() -> None:
    rng = np.random.default_rng(176)
    x, y = rng.normal(size=10), rng.normal(size=10)
    big = sf.minkowski_distance(x, y, 400.0)
    assert big == pytest.approx(sf.chebyshev_distance(x, y), rel=0.01)
    assert sf.chebyshev_distance(x, y) <= big


def test_rejects_an_overflowing_difference() -> None:
    with pytest.raises(ValueError):
        sf.chebyshev_distance([1e308], [-1e308])
