"""The cross-entropy (ADR 0415)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_entropy_plus_the_kl_divergence() -> None:
    rng = np.random.default_rng(165)
    p, q = rng.uniform(0.0, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    pn = p / p.sum()
    entropy = -np.sum(pn * np.log(pn))
    expected = entropy + sf.kl_divergence(p, q)
    assert sf.cross_entropy(p, q) == pytest.approx(expected, rel=1e-12)


def test_is_least_when_q_is_p() -> None:
    rng = np.random.default_rng(166)
    p = rng.uniform(0.1, 1.0, 10)
    for _ in range(5):
        q = rng.uniform(0.1, 1.0, 10)
        assert sf.cross_entropy(p, p) <= sf.cross_entropy(p, q)


def test_rejects_a_zero_q_under_a_positive_p() -> None:
    with pytest.raises(ValueError):
        sf.cross_entropy([1.0, 1.0], [1.0, 0.0])
