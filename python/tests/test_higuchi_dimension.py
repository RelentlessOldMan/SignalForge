"""Higuchi fractal dimension (ADR 0330)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_white_noise_is_close_to_two() -> None:
    x = np.random.default_rng(17).standard_normal(20000)
    assert sf.higuchi_dimension(x, 10) == pytest.approx(2.0, abs=0.03)


def test_brownian_motion_is_close_to_one_and_a_half() -> None:
    x = np.cumsum(np.random.default_rng(18).standard_normal(20000))
    assert sf.higuchi_dimension(x, 10) == pytest.approx(1.5, abs=0.05)


def test_a_slow_sine_is_close_to_one() -> None:
    x = np.sin(2 * np.pi * np.arange(5000) / 1000)
    assert sf.higuchi_dimension(x, 8) == pytest.approx(1.0, abs=1e-3)


def test_rejects_a_constant() -> None:
    with pytest.raises(ValueError):
        sf.higuchi_dimension(np.ones(10), 3)
