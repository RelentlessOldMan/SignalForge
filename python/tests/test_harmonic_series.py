"""Harmonic series (conventions: Spectra, Harmonic series; ADR 0139)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

TONES = np.array([151.0, 299.5, 452.0, 601.0, 1000.0])


def test_order_of_tones_does_not_matter() -> None:
    a = sf.harmonic_series(TONES, 3.0)
    perm = [3, 0, 4, 2, 1]
    b = sf.harmonic_series(TONES[perm], 3.0)
    assert b.fundamental == pytest.approx(a.fundamental, rel=1e-12)
    assert list(b.orders) == list(a.orders[perm])
    assert b.matched == a.matched == 4


def test_scaling_scales_the_fundamental() -> None:
    a = sf.harmonic_series(TONES, 3.0)
    b = sf.harmonic_series(2.5 * TONES, 7.5)
    assert b.fundamental == pytest.approx(2.5 * a.fundamental, rel=1e-12)
    assert list(b.orders) == list(a.orders)


def test_clipped_sine_from_find_tones() -> None:
    n, fs, f0 = 4096, 4096.0, 210.3
    t = np.arange(n) / fs
    x = np.clip(np.sin(2 * np.pi * f0 * t), -0.7, 0.7) * np.hanning(n)
    psd = np.abs(np.fft.rfft(x)) ** 2
    tones = sf.find_tones(np.fft.rfftfreq(n, 1 / fs), psd, 4)
    got = sf.harmonic_series([v.frequency for v in tones], 1.0)
    assert got.matched == 4
    assert all(o % 2 == 1 for o in got.orders)  # a symmetric clip adds odd harmonics
    assert got.fundamental == pytest.approx(f0, abs=0.02)
