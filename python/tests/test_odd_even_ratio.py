"""Odd-to-even harmonic ratio (conventions: Spectra, Odd-to-even ratio; ADR 0141)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

HEIGHTS = np.array([5.0, 3.0, 2.0, 1.0, 0.5])
ORDERS = np.array([1, 2, 3, 4, 0])


def test_scaling_heights_leaves_it_unchanged() -> None:
    a = sf.odd_even_ratio(HEIGHTS, ORDERS)
    assert sf.odd_even_ratio(6.0 * HEIGHTS, ORDERS) == pytest.approx(a, rel=1e-12)


def test_permuting_tones_leaves_it_unchanged() -> None:
    perm = [4, 2, 0, 3, 1]
    a = sf.odd_even_ratio(HEIGHTS, ORDERS)
    assert sf.odd_even_ratio(HEIGHTS[perm], ORDERS[perm]) == pytest.approx(a, rel=1e-12)


def test_clipped_sine_is_odd_only() -> None:
    n, fs, f0 = 4096, 4096.0, 210.3
    t = np.arange(n) / fs
    x = np.clip(np.sin(2 * np.pi * f0 * t), -0.7, 0.7) * np.hanning(n)
    psd = np.abs(np.fft.rfft(x)) ** 2
    tones = sf.find_tones(np.fft.rfftfreq(n, 1 / fs), psd, 4)
    series = sf.harmonic_series([v.frequency for v in tones], 1.0)
    assert sf.odd_even_ratio([v.height for v in tones], series.orders) == math.inf
