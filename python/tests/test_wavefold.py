"""Wavefolder (ADR 0252)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_inside_unchanged_and_bounded() -> None:
    x = np.random.default_rng(27).uniform(-10, 10, 2000)
    y = sf.wavefold(x, 1.5)
    assert np.max(np.abs(y)) <= 1.5
    inside = np.abs(x) <= 1.5
    assert np.allclose(y[inside], x[inside], rtol=0, atol=1e-15)


def test_ramp_gives_a_triangle() -> None:
    x = np.arange(0, 801) / 100
    y = sf.wavefold(x, 1.0)
    assert np.allclose(np.abs(np.diff(y)), 0.01, rtol=0, atol=1e-12)


def test_rejects_zero_limit() -> None:
    with pytest.raises(ValueError):
        sf.wavefold([1.0], 0.0)
