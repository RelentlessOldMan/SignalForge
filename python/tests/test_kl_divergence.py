"""The Kullback-Leibler divergence (ADR 0407)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_cross_entropy_less_the_entropy() -> None:
    rng = np.random.default_rng(151)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    pn, qn = p / p.sum(), q / q.sum()
    expected = -np.sum(pn * np.log(qn)) + np.sum(pn * np.log(pn))
    assert sf.kl_divergence(p, q) == pytest.approx(expected, rel=1e-12)


def test_drops_the_zeros_of_p() -> None:
    assert sf.kl_divergence([0.0, 1.0, 1.0], [5.0, 1.0, 1.0]) == pytest.approx(
        np.log(7.0 / 2.0), rel=1e-14
    )


def test_rejects_a_zero_q_under_a_positive_p() -> None:
    with pytest.raises(ValueError):
        sf.kl_divergence([1.0, 1.0], [1.0, 0.0])
