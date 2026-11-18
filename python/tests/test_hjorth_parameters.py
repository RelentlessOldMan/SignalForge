"""Hjorth parameters (ADR 0324)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_has_mobility_from_its_frequency_and_complexity_one() -> None:
    # Over whole cycles, the first difference of sin(w n) is 2 sin(w/2) times a shifted sine.
    w = 2 * math.pi * 5 / 400
    h = sf.hjorth_parameters(3.0 * np.sin(w * np.arange(4000)))
    assert h.activity == pytest.approx(4.5, rel=1e-3)
    assert h.mobility == pytest.approx(2 * math.sin(w / 2), rel=1e-3)
    assert h.complexity == pytest.approx(1.0, rel=1e-3)


def test_white_noise_is_more_complex_than_a_sine() -> None:
    x = np.random.default_rng(3).standard_normal(20000)
    h = sf.hjorth_parameters(x)
    # var(d) = 2, var(dd) = 6 for unit white noise.
    assert h.mobility == pytest.approx(math.sqrt(2), rel=0.03)
    assert h.complexity == pytest.approx(math.sqrt(3) / math.sqrt(2), rel=0.03)


def test_scaling_changes_activity_only() -> None:
    x = np.array([0.3, -1.2, 2.0, 0.7, -0.4])
    a, b = sf.hjorth_parameters(x), sf.hjorth_parameters(-7 * x + 5)
    assert b.activity == pytest.approx(49 * a.activity)
    assert b.mobility == pytest.approx(a.mobility)
    assert b.complexity == pytest.approx(a.complexity)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.hjorth_parameters([1j, 0, 1])
