"""Goodman and Kruskal's gamma (ADR 0377)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_for_a_coarse_monotone_pair() -> None:
    x = np.random.default_rng(99).integers(0, 4, 200).astype(float)
    assert sf.goodman_kruskal_gamma(x, 3 * x + 1) == 1.0
    assert sf.goodman_kruskal_gamma(x, -x) == -1.0


def test_matches_tau_without_ties() -> None:
    rng = np.random.default_rng(100)
    x = rng.standard_normal(80)
    y = x + rng.standard_normal(80)
    assert sf.goodman_kruskal_gamma(x, y) == pytest.approx(sf.kendall_tau(x, y), abs=1e-12)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.goodman_kruskal_gamma([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])
