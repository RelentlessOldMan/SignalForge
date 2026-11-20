"""The Russell-Rao coefficient (ADR 0426)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_at_most_the_jaccard_and_simple_matching() -> None:
    rng = np.random.default_rng(185)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = 1.0
        rr = sf.russell_rao_coefficient(t, d)
        assert rr <= sf.jaccard_index(t, d)
        assert rr <= sf.simple_matching_coefficient(t, d)


def test_is_the_joint_rate() -> None:
    t = np.array([1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0])
    d = np.array([1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0])
    assert sf.russell_rao_coefficient(t, d) == pytest.approx(float(np.mean(t * d)), rel=1e-15)


def test_rejects_a_value_other_than_zero_or_one() -> None:
    with pytest.raises(ValueError):
        sf.russell_rao_coefficient([1.0, 0.5], [1.0, 0.0])
