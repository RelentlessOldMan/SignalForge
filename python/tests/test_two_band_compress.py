"""Two-band compressor (ADR 0287)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_loud_bass_does_not_turn_down_the_treble() -> None:
    fs = 8000.0
    n = np.arange(16000)
    bass = 1.0 * np.sin(2 * np.pi * 100.0 * n / fs)
    treble = 0.1 * np.sin(2 * np.pi * 3000.0 * n / fs)
    y = sf.two_band_compress(bass + treble, 8, 800.0, fs, -20.0, 10.0, -20.0, 10.0, 0.99, 0.999)
    tail = y[8000:]
    spectrum = np.abs(np.fft.rfft(tail)) / (tail.size / 2)
    assert spectrum[100] < 0.5
    assert spectrum[3000] == pytest.approx(0.1, rel=0.05)


def test_matches_compress_of_the_bands() -> None:
    rng = np.random.default_rng(53)
    x = rng.standard_normal(400)
    b = sf.crossover_split(x, 4, 0.1, 1.0)
    want = sf.compress(b.low, -6.0, 3.0, 0.3, 0.9) + sf.compress(b.high, -3.0, 2.0, 0.3, 0.9)
    got = sf.two_band_compress(x, 4, 0.1, 1.0, -6.0, 3.0, -3.0, 2.0, 0.3, 0.9)
    assert np.array_equal(got, want)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.two_band_compress([1j], 4, 1.0, 8.0, 0.0, 2.0, 0.0, 2.0, 0.5, 0.5)
