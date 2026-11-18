"""Karplus-Strong pluck (ADR 0304)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_partials_are_harmonics_of_the_loop() -> None:
    rng = np.random.default_rng(304)
    y = sf.karplus_strong(rng.uniform(-1, 1, 79), 79, 16000, 0.996)
    s = np.abs(np.fft.rfft(y))
    peak = (int(np.argmax(s[100:])) + 100) / 2
    harmonic = round(peak / (8000 / 79.5))
    assert harmonic >= 1
    assert abs(peak - harmonic * 8000 / 79.5) < 1.0


def test_the_note_dies_away() -> None:
    rng = np.random.default_rng(3040)
    y = sf.karplus_strong(rng.uniform(-1, 1, 50), 50, 20000, 0.95)
    assert np.sum(y[18000:] ** 2) < 1e-6 * np.sum(y[:2000] ** 2)


def test_rejects_complex_excitation() -> None:
    with pytest.raises(ValueError):
        sf.karplus_strong([1j], 2, 8, 0.9)
