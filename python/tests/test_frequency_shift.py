"""Frequency shifter (ADR 0301)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_harmonics_move_by_the_same_hertz() -> None:
    n = np.arange(8000)
    x = np.cos(2 * np.pi * 100 * n / 8000) + 0.5 * np.cos(2 * np.pi * 200 * n / 8000)
    s = np.abs(np.fft.rfft(sf.frequency_shift(x, 30.0, 8000.0)))
    assert s[130] == pytest.approx(4000, rel=1e-9)
    assert s[230] == pytest.approx(2000, rel=1e-9)
    assert s[70] < 1e-6 and s[100] < 1e-6 and s[200] < 1e-6


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.frequency_shift([1j, 1.0], 1.0, 8.0)
