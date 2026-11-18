"""Octave-up effect (ADR 0289)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_moves_up_an_octave() -> None:
    n = np.arange(4096)
    x = np.sin(2 * np.pi * 64 * n / 4096)
    y = sf.octave_up(x, 0.999, 1.0)
    s = np.abs(np.fft.rfft(y[2048:] * np.hanning(2048)))
    assert s[32] < 1e-3 * s[64]
    assert int(np.argmax(s[1:])) + 1 == 64


def test_mix_zero_is_the_input() -> None:
    x = np.array([0.3, -0.7, 1.1])
    assert np.array_equal(sf.octave_up(x, 0.5, 0.0), x)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.octave_up([1j], 0.5, 0.5)
