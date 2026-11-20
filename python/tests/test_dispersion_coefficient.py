"""The dispersion coefficient (ADR 0471)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_population_covariance() -> None:
    rng = np.random.default_rng(234)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.dispersion_coefficient(t, d)
        cov = float(np.mean(t * d) - np.mean(t) * np.mean(d))
        assert v == pytest.approx(cov, abs=1e-15)
        assert v == sf.dispersion_coefficient(d, t)
        assert -0.25 <= v <= 0.25


def test_is_zero_for_a_constant_record() -> None:
    assert sf.dispersion_coefficient([1.0, 1.0, 1.0], [1.0, 0.0, 1.0]) == 0.0


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.dispersion_coefficient([0.0, 1.0], [1.0])
