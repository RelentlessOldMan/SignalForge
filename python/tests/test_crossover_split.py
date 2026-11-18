"""Two-band splitter (ADR 0285)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_sum_has_a_flat_magnitude() -> None:
    x = np.zeros(8192)
    x[0] = 1.0
    b = sf.crossover_split(x, 4, 0.05, 1.0)
    spectrum = np.abs(np.fft.rfft(b.low + b.high))
    assert spectrum == pytest.approx(np.ones(spectrum.size), abs=1e-9)


def test_bands_separate_two_tones() -> None:
    n = np.arange(8000)
    lo_tone = np.sin(2 * np.pi * 100.0 * n / 8000.0)
    hi_tone = np.sin(2 * np.pi * 3000.0 * n / 8000.0)
    b = sf.crossover_split(lo_tone + hi_tone, 8, 800.0, 8000.0)
    tail = slice(4000, None)
    assert np.max(np.abs(np.fft.rfft(b.low[tail]))[1000:]) < 1e-2 * np.max(
        np.abs(np.fft.rfft(b.low[tail]))
    )
    assert np.max(np.abs(np.fft.rfft(b.high[tail]))[:300]) < 1e-2 * np.max(
        np.abs(np.fft.rfft(b.high[tail]))
    )


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.crossover_split([1j, 2.0], 4, 1.0, 8.0)
