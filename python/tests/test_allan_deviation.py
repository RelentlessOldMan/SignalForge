"""Allan deviation (ADR 0327)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_white_frequency_noise_falls_as_one_over_root_tau() -> None:
    y = np.random.default_rng(11).standard_normal(200000) * 1e-9
    a = sf.allan_deviation(y, 0.01, [1, 10, 100])
    assert np.allclose(a.taus, [0.01, 0.1, 1.0])
    for m, s in zip([1, 10, 100], a.deviations, strict=True):
        assert s == pytest.approx(1e-9 / math.sqrt(m), rel=0.05)


def test_drift_gives_d_tau_over_root_two() -> None:
    drift = 3e-7
    y = drift * 0.1 * np.arange(500)
    a = sf.allan_deviation(y, 0.1, [1, 7, 250])
    assert np.allclose(a.deviations, drift * a.taus / math.sqrt(2), rtol=1e-9, atol=0)


def test_rejects_a_float_factor() -> None:
    with pytest.raises(ValueError):
        sf.allan_deviation([0.0, 1.0, 2.0, 3.0], 1.0, [1.0])  # type: ignore[list-item]
