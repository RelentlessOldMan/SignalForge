"""Ring modulator (ADR 0260)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_moves_a_tone_to_the_sum_and_difference() -> None:
    fs, n = 8000.0, 8000
    x = sf.tone(fs, n, 1000.0, complex=False)
    y = sf.ring_modulate(x, 300.0, fs)
    s = np.abs(np.fft.rfft(np.real(y))) / (n / 2)
    assert abs(s[700] - 0.5) < 1e-9 and abs(s[1300] - 0.5) < 1e-9
    s[[700, 1300]] = 0
    assert np.max(s) < 1e-9


def test_complex_keeps_kind() -> None:
    y = sf.ring_modulate(np.array([1 + 1j, 2j]), 0.0, 1.0)
    assert y.dtype == np.complex128
    assert np.array_equal(y, [1 + 1j, 2j])
