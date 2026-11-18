"""Vibrato (ADR 0271)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_constant_delay_matches_a_shift() -> None:
    rng = np.random.default_rng(38)
    x = rng.standard_normal(100)
    y = np.real(sf.vibrato(x, 5.0, 0.0, 1.0, 100.0))
    assert np.array_equal(y[5:], x[:-5])
    assert np.all(y[:5] == 0)


def test_pitch_swings_around_the_tone() -> None:
    fs, f0 = 8000.0, 500.0
    n = np.arange(16000)
    x = np.cos(2 * np.pi * f0 * n / fs)
    y = np.real(sf.vibrato(x, 40.0, 30.0, 2.0, fs))
    # the instantaneous frequency is f0 (1 - d'(n)), so the peak shift is
    # f0 * depth * 2 pi rate / fs = 500 * 30 * 4 pi / 8000, about 23.6 Hz
    spectrum = np.abs(np.fft.rfft(y[4000:12000] * np.hanning(8000)))
    freqs = np.fft.rfftfreq(8000, 1 / fs)
    band = spectrum[(freqs > 440) & (freqs < 560)].sum() / spectrum.sum()
    assert band > 0.95


def test_rejects_depth_above_delay() -> None:
    with pytest.raises(ValueError):
        sf.vibrato([1.0], 1.0, 2.0, 1.0, 8.0)
