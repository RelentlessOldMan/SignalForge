"""The Minkowski distance (ADR 0419)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_numpy_norm() -> None:
    rng = np.random.default_rng(173)
    x, y = rng.normal(size=20), rng.normal(size=20)
    for order in (1.0, 1.5, 2.0, 3.0, 7.0):
        expected = np.linalg.norm(x - y, ord=order)
        assert sf.minkowski_distance(x, y, order) == pytest.approx(expected, rel=1e-13)


def test_falls_with_order_towards_the_largest_difference() -> None:
    rng = np.random.default_rng(174)
    x, y = rng.normal(size=10), rng.normal(size=10)
    values = [sf.minkowski_distance(x, y, p) for p in (1.0, 2.0, 4.0, 50.0)]
    assert values == sorted(values, reverse=True)
    assert values[-1] == pytest.approx(np.max(np.abs(x - y)), rel=0.05)


def test_rejects_an_order_below_one() -> None:
    with pytest.raises(ValueError):
        sf.minkowski_distance([1.0], [2.0], 0.5)
