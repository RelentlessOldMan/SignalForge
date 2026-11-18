"""Harmonic exciter (ADR 0288)."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf


def test_adds_harmonics_of_a_high_tone_but_not_a_low_one() -> None:
    fs = 8000.0
    n = np.arange(8000)
    hi = 0.8 * np.sin(2 * np.pi * 1000.0 * n / fs)
    lo = 0.8 * np.sin(2 * np.pi * 100.0 * n / fs)
    tail = slice(4000, None)

    def third(y: NDArray[np.float64], f: int) -> float:
        s = np.abs(np.fft.rfft(y[tail])) / 2000
        return float(s[3 * f // 2])

    assert third(sf.exciter(hi, 4, 500.0, fs, 4.0, 1.0), 1000) > 1e-2
    assert third(sf.exciter(lo, 4, 500.0, fs, 4.0, 1.0), 100) < 1e-3


def test_small_signals_add_the_high_band() -> None:
    rng = np.random.default_rng(54)
    x = 1e-4 * rng.standard_normal(300)
    want = x + 0.5 * sf.crossover_split(x, 4, 0.2, 1.0).high
    assert sf.exciter(x, 4, 0.2, 1.0, 2.0, 0.5) == pytest.approx(want, rel=0, abs=1e-10)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.exciter([1j], 4, 1.0, 8.0, 1.0, 0.5)
