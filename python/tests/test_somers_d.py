"""Somers' D (ADR 0378)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_tau_without_ties() -> None:
    rng = np.random.default_rng(101)
    x = rng.standard_normal(80)
    y = x + rng.standard_normal(80)
    assert sf.somers_d(x, y) == pytest.approx(sf.kendall_tau(x, y), abs=1e-12)


def test_the_two_directions_multiply_to_tau_b_squared() -> None:
    rng = np.random.default_rng(102)
    x = rng.integers(0, 4, 120).astype(float)
    y = x + rng.integers(-2, 3, 120)
    tau = sf.kendall_tau(x, y)
    assert sf.somers_d(x, y) * sf.somers_d(y, x) == pytest.approx(tau**2, rel=1e-12)


def test_rejects_a_constant_predictor() -> None:
    with pytest.raises(ValueError):
        sf.somers_d([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
