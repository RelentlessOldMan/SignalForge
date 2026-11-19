"""The log loss (ADR 0392)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_binary_cross_entropy() -> None:
    rng = np.random.default_rng(123)
    p = 0.02 + 0.96 * rng.random(500)
    y = (rng.random(500) < p).astype(float)
    expected = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    assert sf.log_loss(y, p) == pytest.approx(expected, rel=1e-12)


def test_rewards_the_true_probability() -> None:
    rng = np.random.default_rng(124)
    y = (rng.random(20000) < 0.3).astype(float)
    honest = sf.log_loss(y, np.full(y.size, 0.3))
    assert honest < sf.log_loss(y, np.full(y.size, 0.5))
    assert honest < sf.log_loss(y, np.full(y.size, 0.1))


def test_rejects_a_certain_wrong_forecast() -> None:
    with pytest.raises(ValueError):
        sf.log_loss([1.0, 0.0], [0.5, 1.0])
