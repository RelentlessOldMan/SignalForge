"""Permutation entropy (ADR 0325)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_white_noise_is_close_to_one() -> None:
    x = np.random.default_rng(5).standard_normal(50000)
    assert sf.permutation_entropy(x, 4) == pytest.approx(1.0, abs=2e-3)


def test_ignores_gain_and_offset() -> None:
    x = np.random.default_rng(6).standard_normal(500)
    assert sf.permutation_entropy(3 * x + 2, 3, 2) == sf.permutation_entropy(x, 3, 2)


def test_a_sine_is_below_noise() -> None:
    x = np.sin(0.05 * np.arange(2000))
    assert sf.permutation_entropy(x, 3) < 0.5


def test_rejects_a_float_order() -> None:
    with pytest.raises(ValueError):
        sf.permutation_entropy([0.0, 1.0, 2.0], 2.0)  # type: ignore[arg-type]
