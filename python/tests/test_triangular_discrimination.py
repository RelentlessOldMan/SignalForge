"""The triangular discrimination (ADR 0416)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_sits_between_the_hellinger_bounds() -> None:
    rng = np.random.default_rng(167)
    for _ in range(10):
        p, q = rng.integers(0, 5, 20).astype(float), rng.integers(0, 5, 20).astype(float)
        p[0] = q[0] = 1.0
        h2 = sf.hellinger_distance(p, q) ** 2
        t = sf.triangular_discrimination(p, q)
        assert 2 * h2 <= t + 1e-14
        assert t <= 4 * h2 + 1e-14


def test_is_at_most_twice_the_total_variation() -> None:
    rng = np.random.default_rng(168)
    p, q = rng.uniform(0.0, 1.0, 30), rng.uniform(0.0, 1.0, 30)
    assert sf.triangular_discrimination(p, q) <= 2 * sf.total_variation_distance(p, q)


def test_is_symmetric() -> None:
    p, q = [1.0, 2.0, 0.0, 4.0], [3.0, 0.0, 1.0, 1.0]
    assert sf.triangular_discrimination(p, q) == sf.triangular_discrimination(q, p)
