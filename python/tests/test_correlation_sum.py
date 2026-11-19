"""Correlation sum (ADR 0349)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_uniform_noise_fills_its_embedding() -> None:
    # Independent uniform samples in m = 2 fill the square: C(r) ~ r^2 at small r.
    x = np.random.default_rng(53).uniform(size=1500)
    got = sf.correlation_sum(x, 2, [0.02, 0.04, 0.08])
    assert abs(got.dimension - 2) < 0.15


def test_values_rise_with_the_radius() -> None:
    x = np.random.default_rng(54).standard_normal(300)
    got = sf.correlation_sum(x, 2, [0.5, 1.0, 2.0, 4.0])
    assert np.all(np.diff(got.values) >= 0)
    assert got.values[-1] <= 1


def test_rejects_a_radius_below_every_distance() -> None:
    with pytest.raises(ValueError):
        sf.correlation_sum([0.0, 1.0, 2.0], 1, [0.5, 2.0])
