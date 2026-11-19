"""The Pearson chi-square divergence (ADR 0412)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_second_moment_of_the_ratio_less_one() -> None:
    rng = np.random.default_rng(159)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    pn, qn = p / p.sum(), q / q.sum()
    expected = np.sum(pn * pn / qn) - 1
    assert sf.chi_square_divergence(p, q) == pytest.approx(expected, rel=1e-11)


def test_bounds_the_kl_divergence() -> None:
    rng = np.random.default_rng(160)
    p, q = rng.uniform(0.0, 1.0, 30), rng.uniform(0.1, 1.0, 30)
    assert sf.kl_divergence(p, q) <= np.log1p(sf.chi_square_divergence(p, q))


def test_rejects_a_zero_q_under_a_positive_p() -> None:
    with pytest.raises(ValueError):
        sf.chi_square_divergence([1.0, 1.0], [1.0, 0.0])
