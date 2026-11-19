"""Attention entropy (ADR 0346)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_is_zero_and_noise_is_not() -> None:
    sine = np.sin(2 * np.pi * (np.arange(2000) + 0.3) / 40)
    assert sf.attention_entropy(sine) == pytest.approx(0.0, abs=1e-12)
    assert sf.attention_entropy(np.random.default_rng(47).standard_normal(2000)) > 1.0


def test_any_increasing_map_changes_nothing() -> None:
    x = np.random.default_rng(48).standard_normal(300)
    assert sf.attention_entropy(np.exp(x)) == sf.attention_entropy(x)


def test_rejects_a_ramp() -> None:
    with pytest.raises(ValueError):
        sf.attention_entropy(np.arange(10.0))
