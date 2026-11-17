"""Schmitt trigger (ADR 0244)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noisy_sine_switches_once_per_half_cycle() -> None:
    n = np.arange(4000)
    x = np.sin(2 * np.pi * n / 400) + 0.1 * np.random.default_rng(19).standard_normal(4000)
    y = sf.schmitt_trigger(x, -0.5, 0.5)
    assert y.dtype == np.uint8
    assert int(np.count_nonzero(np.diff(y.astype(int)))) == 20


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.schmitt_trigger(np.array([1 + 1j]), 0.0, 1.0)
