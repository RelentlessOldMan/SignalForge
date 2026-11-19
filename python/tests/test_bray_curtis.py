"""The Bray-Curtis dissimilarity (ADR 0418)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_total_variation_for_equal_totals() -> None:
    rng = np.random.default_rng(171)
    x = rng.uniform(0.0, 1.0, 20)
    y = rng.uniform(0.0, 1.0, 20)
    y *= x.sum() / y.sum()
    tv = sf.total_variation_distance(x, y)
    assert sf.bray_curtis(x, y) == pytest.approx(tv, rel=1e-12)


def test_is_symmetric_and_bounded() -> None:
    rng = np.random.default_rng(172)
    x, y = rng.uniform(0.0, 1.0, 20), rng.uniform(0.0, 1.0, 20)
    d = sf.bray_curtis(x, y)
    assert d == sf.bray_curtis(y, x)
    assert 0.0 <= d <= 1.0


def test_rejects_two_zero_vectors() -> None:
    with pytest.raises(ValueError):
        sf.bray_curtis([0.0, 0.0], [0.0, 0.0])
