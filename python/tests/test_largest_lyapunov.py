"""Largest Lyapunov exponent (ADR 0354)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_logistic_map_is_near_ln_2() -> None:
    # The logistic map at r = 4 has the exponent ln 2 per step.
    x = np.empty(1500)
    x[0] = 0.2345
    for i in range(1, x.shape[0]):
        x[i] = 4 * x[i - 1] * (1 - x[i - 1])
    got = sf.largest_lyapunov(x, 2, 4, theiler=5)
    assert abs(got.exponent - np.log(2)) < 0.15


def test_a_sine_does_not_diverge() -> None:
    x = np.sin(2 * np.pi * np.arange(600) / 37.3)
    got = sf.largest_lyapunov(x, 3, 5, delay=3, theiler=10)
    assert abs(got.exponent) < 0.05


def test_rejects_too_few_points() -> None:
    with pytest.raises(ValueError):
        sf.largest_lyapunov([0.0, 1.0, 2.0, 3.0], 1, 1, theiler=1)
