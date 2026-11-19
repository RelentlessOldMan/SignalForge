"""Hoeffding's D (ADR 0374)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_for_any_increasing_map() -> None:
    x = np.random.default_rng(90).standard_normal(60)
    assert sf.hoeffding_d(x, np.exp(x)) == pytest.approx(1.0, abs=1e-12)


def test_sees_a_circle() -> None:
    t = np.random.default_rng(91).uniform(0, 2 * np.pi, 200)
    assert sf.hoeffding_d(np.cos(t), np.sin(t)) > 0.02
    assert abs(sf.pearson_correlation(np.cos(t), np.sin(t))) < 0.2


def test_is_near_zero_for_independent_records() -> None:
    rng = np.random.default_rng(92)
    assert abs(sf.hoeffding_d(rng.standard_normal(500), rng.standard_normal(500))) < 0.01


def test_rejects_four_samples() -> None:
    with pytest.raises(ValueError):
        sf.hoeffding_d([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
