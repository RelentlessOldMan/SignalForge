"""Wavetable oscillator (ADR 0308)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_table_plays_a_sine() -> None:
    table = np.sin(2 * np.pi * np.arange(2048) / 2048)
    y = sf.wavetable(table, 48000.0, 4800, 441.0)
    want = np.sin(2 * np.pi * 441.0 * np.arange(4800) / 48000.0)
    assert np.max(np.abs(y - want)) < 2e-6


def test_rejects_a_complex_table() -> None:
    with pytest.raises(ValueError):
        sf.wavetable([1j], 8000.0, 4, 1000.0)
