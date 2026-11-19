"""Distance correlation (ADR 0372)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_sees_a_relation_pearson_misses() -> None:
    x = np.random.default_rng(85).uniform(-1, 1, 300)
    y = x * x
    assert abs(sf.pearson_correlation(x, y)) < 0.2
    assert sf.distance_correlation(x, y) > 0.4


def test_is_small_for_independent_records() -> None:
    rng = np.random.default_rng(86)
    assert sf.distance_correlation(rng.standard_normal(600), rng.standard_normal(600)) < 0.12


def test_is_one_for_a_linear_map() -> None:
    x = np.random.default_rng(87).standard_normal(50)
    assert sf.distance_correlation(x, 3 - 2 * x) == pytest.approx(1.0, rel=1e-12)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.distance_correlation([1.0, 2.0, 3.0], [4.0, 4.0, 4.0])
