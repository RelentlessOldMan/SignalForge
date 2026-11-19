"""Chatterjee's xi (ADR 0376)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_reaches_the_top_for_a_monotone_pair() -> None:
    x = np.random.default_rng(96).standard_normal(99)
    assert sf.chatterjee_xi(x, np.exp(x)) == pytest.approx(1 - 3 / 100, abs=1e-15)


def test_sees_a_function_of_any_shape() -> None:
    x = np.random.default_rng(97).uniform(-1, 1, 1000)
    assert sf.chatterjee_xi(x, np.cos(6 * x)) > 0.95
    assert abs(sf.pearson_correlation(x, np.cos(6 * x))) < 0.2


def test_is_near_zero_for_independent_records() -> None:
    rng = np.random.default_rng(98)
    assert abs(sf.chatterjee_xi(rng.standard_normal(2000), rng.standard_normal(2000))) < 0.1


def test_rejects_a_constant_y() -> None:
    with pytest.raises(ValueError):
        sf.chatterjee_xi([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])
