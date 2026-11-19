"""The Brier score (ADR 0391)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_squared_error_of_the_forecast() -> None:
    rng = np.random.default_rng(121)
    p = rng.random(500)
    y = (rng.random(500) < p).astype(float)
    assert sf.brier_score(y, p) == pytest.approx(np.mean((p - y) ** 2), rel=1e-13)


def test_rewards_the_true_probability() -> None:
    rng = np.random.default_rng(122)
    y = (rng.random(20000) < 0.3).astype(float)
    honest = sf.brier_score(y, np.full(y.size, 0.3))
    assert honest < sf.brier_score(y, np.full(y.size, 0.5))
    assert honest < sf.brier_score(y, np.full(y.size, 0.1))


def test_rejects_a_probability_outside_the_unit_interval() -> None:
    with pytest.raises(ValueError):
        sf.brier_score([1.0, 0.0], [0.5, float("nan")])
