"""The Canberra distance (ADR 0417)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_ignores_a_common_scale() -> None:
    rng = np.random.default_rng(169)
    x, y = rng.normal(size=20), rng.normal(size=20)
    assert sf.canberra_distance(1e6 * x, 1e6 * y) == pytest.approx(
        sf.canberra_distance(x, y), rel=1e-13
    )


def test_obeys_the_triangle_inequality() -> None:
    rng = np.random.default_rng(170)
    for _ in range(20):
        x, y, z = rng.normal(size=(3, 8))
        d = sf.canberra_distance
        assert d(x, z) <= d(x, y) + d(y, z) + 1e-12


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.canberra_distance([1.0], [1.0, 1.0])
