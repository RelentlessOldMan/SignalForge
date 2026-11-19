"""Ljung-Box statistic (ADR 0359)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_white_noise_is_near_its_degrees_of_freedom() -> None:
    # Q is about chi-squared with h degrees of freedom: mean h, sd sqrt(2h).
    got = [sf.ljung_box(np.random.default_rng(s).standard_normal(1000), 10) for s in range(200)]
    assert abs(np.mean(got) - 10) < 1.0


def test_a_correlated_record_is_large() -> None:
    x = np.cumsum(np.random.default_rng(68).standard_normal(500))
    assert sf.ljung_box(x, 10) > 1000


def test_rejects_constant() -> None:
    with pytest.raises(ValueError):
        sf.ljung_box([1.0, 1.0, 1.0], 1)
