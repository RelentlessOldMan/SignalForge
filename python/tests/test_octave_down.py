"""Octave-down effect (ADR 0291)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_moves_down_an_octave() -> None:
    n = np.arange(4096)
    x = np.sin(2 * np.pi * 64 * (n + 0.5) / 4096)
    s = np.abs(np.fft.rfft(sf.octave_down(x, 1.0)))
    assert int(np.argmax(s)) == 32
    assert s[64] < 1e-6 * s[32]


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.octave_down([1j], 0.5)
