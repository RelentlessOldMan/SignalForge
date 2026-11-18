"""Dispersion entropy (ADR 0341)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_is_near_one_and_a_sine_is_lower() -> None:
    noise = np.random.default_rng(37).standard_normal(5000)
    sine = np.sin(2 * np.pi * np.arange(5000) / 50)
    a = sf.dispersion_entropy(noise, 2, 6)
    assert a > 0.95
    assert sf.dispersion_entropy(sine, 2, 6) < a


def test_scale_and_offset_change_nothing() -> None:
    x = np.random.default_rng(38).standard_normal(400)
    assert sf.dispersion_entropy(4 * x + 7, 3, 4) == pytest.approx(
        sf.dispersion_entropy(x, 3, 4), rel=1e-12
    )


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.dispersion_entropy(np.ones(10), 2, 3)
