"""Harmonic spectral deviation (conventions: Spectra, Harmonic deviation; ADR 0144)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

HEIGHTS = np.array([5.0, 3.0, 2.0, 1.0, 0.5, 0.25, 7.0])
ORDERS = np.array([1, 2, 3, 4, 5, 9, 0])


def test_scaling_heights_leaves_it_unchanged() -> None:
    a = sf.harmonic_deviation(HEIGHTS, ORDERS)
    assert sf.harmonic_deviation(6.0 * HEIGHTS, ORDERS) == pytest.approx(a, rel=1e-12)


def test_linear_fall_deviates_only_at_the_ends() -> None:
    # Amplitudes 12, 11, ..., 1: each inner envelope equals its amplitude, and each end's
    # envelope is half a step off, so the deviation is (1/2 + 1/2) / 78.
    m = np.arange(1, 13)
    a = 13.0 - m
    assert sf.harmonic_deviation(a**2, m) == pytest.approx(1 / 78, rel=1e-12)
