"""Hedges' g (ADR 0398)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_close_to_the_usual_approximation() -> None:
    rng = np.random.default_rng(134)
    x, y = rng.normal(1.0, 1.0, 25), rng.normal(0.0, 1.0, 25)
    m = x.size + y.size - 2
    approx = (1 - 3 / (4 * m - 1)) * sf.cohen_d(x, y)
    assert sf.hedges_g(x, y) == pytest.approx(approx, rel=1e-4)


def test_shrinks_cohen_d() -> None:
    rng = np.random.default_rng(135)
    x, y = rng.normal(0.8, 1.0, 5), rng.normal(0.0, 1.0, 4)
    assert abs(sf.hedges_g(x, y)) < abs(sf.cohen_d(x, y))


def test_rejects_no_spread() -> None:
    with pytest.raises(ValueError):
        sf.hedges_g([1.0, 1.0], [2.0, 2.0])
