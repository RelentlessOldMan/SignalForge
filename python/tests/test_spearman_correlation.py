"""Spearman rank correlation (ADR 0369)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_for_any_increasing_map() -> None:
    x = np.random.default_rng(79).standard_normal(100)
    assert sf.spearman_correlation(x, np.exp(3 * x)) == pytest.approx(1.0, abs=1e-15)


def test_is_near_zero_for_independent_records() -> None:
    rng = np.random.default_rng(80)
    assert abs(sf.spearman_correlation(rng.standard_normal(4000), rng.standard_normal(4000))) < 0.05


def test_rejects_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.spearman_correlation([1.0, 2.0, 3.0], [1.0, 2.0])
