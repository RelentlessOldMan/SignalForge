"""Delay-line pitch shifter (ADR 0302)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_moves_by_the_ratio() -> None:
    n = np.arange(8000)
    x = np.sin(2 * np.pi * 200 * n / 8000)
    s = np.abs(np.fft.rfft(sf.pitch_shift(x, 1.5, 400.0)))
    assert int(np.argmax(s)) == 300
    assert s[200] < 0.05 * s[300]


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.pitch_shift([1j], 1.5, 8.0)
