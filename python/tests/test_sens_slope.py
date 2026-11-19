"""Sen's slope (ADR 0365)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_finds_a_trend_in_heavy_tailed_noise() -> None:
    rng = np.random.default_rng(73)
    x = 0.01 * np.arange(500) + rng.standard_cauchy(500)
    assert sf.sens_slope(x) == pytest.approx(0.01, abs=0.003)


def test_ignores_one_wild_sample() -> None:
    x = 0.25 * np.arange(20.0)
    x[7] = 1e6
    assert sf.sens_slope(x) == 0.25


def test_rejects_one_sample() -> None:
    with pytest.raises(ValueError):
        sf.sens_slope([1.0])
