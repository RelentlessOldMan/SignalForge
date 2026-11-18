"""Rectifier (ADR 0253)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_full_wave_mean_of_a_sine() -> None:
    n = np.arange(10000)
    y = sf.rectify(np.sin(2 * np.pi * n / 100))
    assert abs(np.mean(y) - 2 / np.pi) < 1e-3


def test_half_wave_plus_negated_half_is_full() -> None:
    x = np.random.default_rng(28).standard_normal(500)
    assert np.array_equal(sf.rectify(x, full=False) + sf.rectify(-x, full=False), sf.rectify(x))


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.rectify(np.array([1j]))
