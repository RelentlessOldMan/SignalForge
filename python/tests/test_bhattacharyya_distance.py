"""The Bhattacharyya distance (ADR 0410)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_ties_to_the_hellinger_distance() -> None:
    rng = np.random.default_rng(156)
    p, q = rng.uniform(0.0, 1.0, 20), rng.uniform(0.0, 1.0, 20)
    h = sf.hellinger_distance(p, q)
    assert sf.bhattacharyya_distance(p, q) == pytest.approx(-np.log(1 - h * h), rel=1e-10)


def test_adds_over_independent_features() -> None:
    p1, q1 = np.array([1.0, 2.0, 3.0]), np.array([3.0, 2.0, 1.0])
    p2, q2 = np.array([1.0, 4.0]), np.array([2.0, 1.0])
    joint = sf.bhattacharyya_distance(np.outer(p1, p2).ravel(), np.outer(q1, q2).ravel())
    parts = sf.bhattacharyya_distance(p1, q1) + sf.bhattacharyya_distance(p2, q2)
    assert joint == pytest.approx(parts, rel=1e-13)


def test_rejects_disjoint_support() -> None:
    with pytest.raises(ValueError):
        sf.bhattacharyya_distance([1.0, 0.0], [0.0, 1.0])
