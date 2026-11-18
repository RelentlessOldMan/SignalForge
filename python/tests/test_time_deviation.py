"""Time deviation (ADR 0331)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_white_phase_noise_is_its_averaged_standard_deviation() -> None:
    # Time error x with white noise of s seconds per sample, y = diff(x) / tau0: TDEV(tau) is
    # s / sqrt(m) for white phase noise, the standard deviation of an m-sample mean.
    tau0, s = 0.01, 2e-9
    x = s * np.random.default_rng(19).standard_normal(200001)
    t = sf.time_deviation(np.diff(x) / tau0, tau0, [1, 16, 64])
    assert np.allclose(t.deviations, s / np.sqrt([1, 16, 64]), rtol=0.06)


def test_is_mdev_scaled() -> None:
    y = np.random.default_rng(20).standard_normal(40)
    mod = sf.modified_allan_deviation(y, 0.5, [1, 4, 13])
    t = sf.time_deviation(y, 0.5, [1, 4, 13])
    assert np.array_equal(t.taus, mod.taus)
    assert np.allclose(t.deviations, mod.taus * mod.deviations / math.sqrt(3), rtol=1e-14)


def test_rejects_too_large_a_factor() -> None:
    with pytest.raises(ValueError):
        sf.time_deviation([0.0, 1.0, 2.0, 3.0], 1.0, [2])
