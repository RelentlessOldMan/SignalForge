"""Slope entropy (ADR 0347)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_is_less_regular_than_a_sine() -> None:
    noise = np.random.default_rng(49).standard_normal(3000)
    sine = 3 * np.sin(2 * np.pi * np.arange(3000) / 60)
    assert sf.slope_entropy(sine, 4, 0.2, 0.01) < sf.slope_entropy(noise, 4, 0.2, 0.01)


def test_an_offset_changes_nothing() -> None:
    x = np.round(np.random.default_rng(50).standard_normal(400) * 64) / 64
    assert sf.slope_entropy(x + 4, 3) == sf.slope_entropy(x, 3)


def test_rejects_delta_above_gamma() -> None:
    with pytest.raises(ValueError):
        sf.slope_entropy([0.0, 1.0, 2.0], 2, 0.5, 1.0)
