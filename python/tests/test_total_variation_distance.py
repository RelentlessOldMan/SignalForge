"""The total variation distance (ADR 0411)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

import signalforge as sf


def test_is_the_largest_event_difference() -> None:
    rng = np.random.default_rng(157)
    p, q = rng.uniform(0.0, 1.0, 8), rng.uniform(0.0, 1.0, 8)
    pn, qn = p / p.sum(), q / q.sum()
    best = max(
        abs(np.sum(pn[list(s)]) - np.sum(qn[list(s)]))
        for r in range(9)
        for s in itertools.combinations(range(8), r)
    )
    assert sf.total_variation_distance(p, q) == pytest.approx(best, rel=1e-13)


def test_is_bounded_by_the_hellinger_distance() -> None:
    rng = np.random.default_rng(158)
    p, q = rng.integers(0, 5, 30).astype(float), rng.integers(0, 5, 30).astype(float)
    h = sf.hellinger_distance(p, q)
    tv = sf.total_variation_distance(p, q)
    assert h * h <= tv + 1e-15
    assert tv <= h * np.sqrt(2 - h * h) + 1e-15


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.total_variation_distance([1.0], [1.0, 1.0])
