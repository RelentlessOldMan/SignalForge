"""Recurrence quantification (ADR 0350)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_is_more_deterministic_than_noise() -> None:
    t = np.arange(800)
    sine = np.sin(2 * np.pi * t / 37)
    noise = np.random.default_rng(55).uniform(-1, 1, 800)
    a = sf.recurrence_quantification(sine, 3, 0.2, delay=4)
    b = sf.recurrence_quantification(noise, 3, 0.2, delay=4)
    assert a.determinism > 0.9
    assert b.determinism < a.determinism


def test_min_line_one_gives_full_determinism() -> None:
    x = np.random.default_rng(56).standard_normal(200)
    got = sf.recurrence_quantification(x, 2, 0.5, min_line=1)
    assert got.determinism == 1.0
    assert 0 < got.rate < 1


def test_rejects_no_recurrence() -> None:
    with pytest.raises(ValueError):
        sf.recurrence_quantification([0.0, 1.0, 2.0], 1, 0.5)
