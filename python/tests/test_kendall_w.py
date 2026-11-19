"""Kendall's W (ADR 0379)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_mean_spearman_correlation_without_ties() -> None:
    rng = np.random.default_rng(103)
    common = rng.standard_normal(30)
    rows = common + rng.standard_normal((6, 30))
    rs = [sf.spearman_correlation(rows[i], rows[j]) for i, j in itertools.combinations(range(6), 2)]
    expected = (5 * np.mean(rs) + 1) / 6
    assert sf.kendall_w(rows) == pytest.approx(expected, abs=1e-12)


def test_does_not_depend_on_the_order_of_the_items() -> None:
    rng = np.random.default_rng(104)
    rows = rng.integers(0, 5, (4, 20)).astype(float)
    order = rng.permutation(20)
    assert sf.kendall_w(rows[:, order]) == pytest.approx(sf.kendall_w(rows), abs=1e-14)


def test_rejects_one_dimensional_ratings() -> None:
    with pytest.raises(ValueError):
        sf.kendall_w([1.0, 2.0, 3.0])


def test_rejects_ragged_rows() -> None:
    with pytest.raises(ValueError):
        sf.kendall_w([[1.0, 2.0, 3.0], [1.0, 2.0]])
