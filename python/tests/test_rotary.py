"""Rotary-speaker effect (ADR 0292)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_tremolo_and_vibrato_of_the_bands() -> None:
    rng = np.random.default_rng(55)
    x = rng.standard_normal(500)
    b = sf.crossover_split(x, 4, 0.1, 1.0)
    horn = sf.tremolo(sf.vibrato(b.high, 4.0, 3.0, 0.01, 1.0), 0.01, 0.6, 1.0)
    drum = sf.tremolo(b.low, 0.002, 0.6, 1.0)
    got = sf.rotary(x, 4, 0.1, 0.01, 0.002, 4.0, 3.0, 0.6, 1.0)
    assert np.array_equal(got, horn + drum)


def test_the_horn_swells_a_treble_tone() -> None:
    fs = 8000.0
    n = np.arange(16000)
    x = np.sin(2 * np.pi * 2000.0 * n / fs)
    y = sf.rotary(x, 8, 800.0, 1.0, 0.8, 10.0, 5.0, 0.8, fs)
    loud = np.max(np.abs(y[7900:8100]))
    quiet = np.max(np.abs(y[11900:12100]))
    assert loud > 0.9
    assert quiet < 0.3


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.rotary([1j], 4, 1.0, 0.1, 0.1, 2.0, 1.0, 0.5, 8.0)
