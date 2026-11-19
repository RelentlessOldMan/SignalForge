"""Bubble entropy (ADR 0345)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_is_less_regular_than_a_sine() -> None:
    noise = np.random.default_rng(45).standard_normal(3000)
    sine = np.sin(2 * np.pi * np.arange(3000) / 60)
    assert sf.bubble_entropy(sine, 10) < sf.bubble_entropy(noise, 10)


def test_any_increasing_map_changes_nothing() -> None:
    x = np.random.default_rng(46).standard_normal(400)
    assert sf.bubble_entropy(np.exp(x), 6) == sf.bubble_entropy(x, 6)


def test_rejects_m_one() -> None:
    with pytest.raises(ValueError):
        sf.bubble_entropy([0.0, 1.0, 2.0], 1)
