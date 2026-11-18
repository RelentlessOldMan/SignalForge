"""Bass enhancer (ADR 0290)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_adds_the_third_harmonic_of_a_bass_note() -> None:
    fs = 8000.0
    n = np.arange(8000)
    x = 0.8 * np.sin(2 * np.pi * 50.0 * n / fs)
    y = sf.bass_enhancer(x, 4, 100.0, fs, 4.0, 1.0)
    s = np.abs(np.fft.rfft((y - x)[4000:])) / 2000
    assert s[75] > 1e-2
    assert s[25] < 0.5 * s[75]


def test_a_high_tone_is_left_alone() -> None:
    fs = 8000.0
    n = np.arange(8000)
    x = 0.5 * np.sin(2 * np.pi * 2000.0 * n / fs)
    y = sf.bass_enhancer(x, 8, 100.0, fs, 4.0, 1.0)
    assert np.max(np.abs((y - x)[4000:])) < 1e-6


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.bass_enhancer([1j], 4, 1.0, 8.0, 1.0, 0.5)
