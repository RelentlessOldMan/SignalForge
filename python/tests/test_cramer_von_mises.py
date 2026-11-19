"""The two-sample Cramer-von Mises statistic (ADR 0405)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_pooled_sum_of_squared_gaps() -> None:
    rng = np.random.default_rng(147)
    x, y = np.round(rng.normal(0.4, 1.0, 50), 1), np.round(rng.normal(0.0, 2.0, 35), 1)
    z = np.concatenate([x, y])[:, None]
    gaps = np.mean(x <= z, axis=1) - np.mean(y <= z, axis=1)
    expected = x.size * y.size / z.size**2 * np.sum(gaps**2)
    assert sf.cramer_von_mises(x, y) == pytest.approx(expected, rel=1e-12)


def test_matches_the_rank_formula_without_ties() -> None:
    rng = np.random.default_rng(148)
    x, y = rng.normal(0.3, 1.0, 30), rng.normal(0.0, 1.0, 20)
    nx, ny = x.size, y.size
    n = nx + ny
    ranks = np.argsort(np.argsort(np.concatenate([x, y]))) + 1
    rx, ry = np.sort(ranks[:nx]), np.sort(ranks[nx:])
    u = nx * np.sum((rx - np.arange(1, nx + 1)) ** 2) + ny * np.sum(
        (ry - np.arange(1, ny + 1)) ** 2
    )
    expected = u / (nx * ny * n) - (4 * nx * ny - 1) / (6 * n)
    assert sf.cramer_von_mises(x, y) == pytest.approx(expected, rel=1e-12)


def test_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        sf.cramer_von_mises([], [1.0])
