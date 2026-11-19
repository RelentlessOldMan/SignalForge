"""Kendall's tau-b (ADR 0370)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_for_any_increasing_map() -> None:
    x = np.random.default_rng(81).standard_normal(80)
    assert sf.kendall_tau(x, np.tanh(x)) == pytest.approx(1.0, abs=1e-15)


def test_matches_the_normal_relation_to_correlation() -> None:
    rng = np.random.default_rng(82)
    a = rng.standard_normal(3000)
    b = 0.6 * a + 0.8 * rng.standard_normal(3000)
    # For a bivariate normal pair, tau = (2/pi) asin(rho).
    assert sf.kendall_tau(a, b) == pytest.approx(2 / np.pi * np.arcsin(0.6), abs=0.03)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.kendall_tau([1.0, 2.0, 3.0], [4.0, 4.0, 4.0])
