"""Increment entropy (ADR 0344)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_is_less_regular_than_a_sine() -> None:
    noise = np.random.default_rng(43).standard_normal(3000)
    sine = np.sin(2 * np.pi * np.arange(3000) / 60)
    assert sf.increment_entropy(sine, 2, 4) < sf.increment_entropy(noise, 2, 4)


def test_scale_and_offset_change_nothing() -> None:
    x = np.random.default_rng(44).standard_normal(500)
    assert sf.increment_entropy(2 * x - 1, 3, 4) == pytest.approx(
        sf.increment_entropy(x, 3, 4), rel=1e-12
    )


def test_rejects_a_ramp() -> None:
    with pytest.raises(ValueError):
        sf.increment_entropy(np.arange(10.0), 2, 4)
