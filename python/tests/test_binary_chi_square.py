"""The chi-square statistic of two binary records (ADR 0478)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_n_times_the_squared_matthews_correlation() -> None:
    rng = np.random.default_rng(241)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        v = sf.binary_chi_square(t, d)
        assert v == pytest.approx(25 * sf.matthews_correlation(t, d) ** 2, rel=1e-13)
        assert v == sf.binary_chi_square(d, t)
        assert 0.0 <= v <= 25.0


def test_matches_the_expected_count_formula() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    obs = np.array(
        [[np.sum(t * d), np.sum(t * (1 - d))], [np.sum((1 - t) * d), np.sum((1 - t) * (1 - d))]]
    )
    exp = np.outer(obs.sum(axis=1), obs.sum(axis=0)) / obs.sum()
    assert sf.binary_chi_square(t, d) == pytest.approx(
        float(np.sum((obs - exp) ** 2 / exp)), rel=1e-13
    )


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.binary_chi_square([1.0, 1.0], [1.0, 0.0])
