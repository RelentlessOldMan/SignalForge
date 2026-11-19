"""The first Wasserstein distance (ADR 0403)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_equal_sizes_pair_the_sorted_values() -> None:
    rng = np.random.default_rng(143)
    x, y = rng.normal(0.4, 1.0, 50), rng.normal(0.0, 2.0, 50)
    expected = np.mean(np.abs(np.sort(x) - np.sort(y)))
    assert sf.wasserstein_distance(x, y) == pytest.approx(expected, rel=1e-12)


def test_is_symmetric_and_moves_with_a_shift() -> None:
    rng = np.random.default_rng(144)
    x, y = rng.normal(0.3, 1.0, 30), rng.normal(0.0, 1.0, 20)
    assert sf.wasserstein_distance(y, x) == pytest.approx(sf.wasserstein_distance(x, y))
    assert sf.wasserstein_distance(x, x + 2.5) == pytest.approx(2.5, rel=1e-12)


def test_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        sf.wasserstein_distance([1.0], [])
