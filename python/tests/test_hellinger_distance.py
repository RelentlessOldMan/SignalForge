"""The Hellinger distance (ADR 0409)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_bhattacharyya_coefficient_form() -> None:
    rng = np.random.default_rng(154)
    p, q = rng.uniform(0.0, 1.0, 20), rng.uniform(0.0, 1.0, 20)
    bc = np.sum(np.sqrt(p / p.sum() * q / q.sum()))
    assert sf.hellinger_distance(p, q) == pytest.approx(np.sqrt(1 - bc), rel=1e-10)


def test_is_symmetric_and_bounded() -> None:
    rng = np.random.default_rng(155)
    p, q = rng.integers(0, 5, 30).astype(float), rng.integers(0, 5, 30).astype(float)
    assert sf.hellinger_distance(q, p) == sf.hellinger_distance(p, q)
    assert 0 <= sf.hellinger_distance(p, q) <= 1


def test_rejects_a_negative_weight() -> None:
    with pytest.raises(ValueError):
        sf.hellinger_distance([1.0, -1.0], [1.0, 1.0])
