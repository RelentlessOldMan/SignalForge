"""Auto mutual information (ADR 0352)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_has_little_information_at_any_lag() -> None:
    x = np.random.default_rng(58).standard_normal(20000)
    got = sf.auto_mutual_information(x, [0, 1, 5], 8)
    assert got[0] > 1.0
    # The histogram estimate is biased up by about (B - 1)^2 / (2n) nats.
    assert np.all(got[1:] < 0.01)


def test_a_slow_sine_loses_information_with_lag() -> None:
    x = np.sin(2 * np.pi * np.arange(4000) / 200)
    got = sf.auto_mutual_information(x, [1, 10, 50], 16)
    assert got[0] > got[1] > got[2]


def test_rejects_a_lag_past_the_end() -> None:
    with pytest.raises(ValueError):
        sf.auto_mutual_information([0.0, 1.0, 2.0], [3])
