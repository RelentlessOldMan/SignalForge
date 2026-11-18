"""Hadamard deviation (ADR 0329)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_drift_cancels_where_it_dominates_the_allan_deviation() -> None:
    rng = np.random.default_rng(15)
    y = 1e-9 * rng.standard_normal(20000) + 1e-10 * np.arange(20000)
    # At m = 100 the drift gives an Allan deviation of 1e-8 / sqrt 2; the noise alone 1e-10.
    a = sf.allan_deviation(y, 1.0, [100]).deviations[0]
    h = sf.hadamard_deviation(y, 1.0, [100]).deviations[0]
    assert a > 5e-9
    assert h == pytest.approx(1e-9 / math.sqrt(100), rel=0.3)


def test_white_frequency_noise_matches_the_allan_variance() -> None:
    y = np.random.default_rng(16).standard_normal(100000)
    h = sf.hadamard_deviation(y, 1.0, [1, 10, 50]).deviations
    assert np.allclose(h, 1 / np.sqrt([1, 10, 50]), rtol=0.06)


def test_rejects_too_large_a_factor() -> None:
    with pytest.raises(ValueError):
        sf.hadamard_deviation([0.0, 1.0, 2.0, 3.0, 4.0], 1.0, [2])
