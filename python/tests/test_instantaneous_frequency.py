"""Instantaneous frequency (conventions: Instantaneous frequency; ADR 0187)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_an_fm_tone_follows_its_modulation() -> None:
    n = np.arange(512)
    fs, fc, dev, fm = 512.0, 100.0, 20.0, 4.0
    phase = 2 * np.pi * fc * n / fs + (dev / fm) * np.sin(2 * np.pi * fm * n / fs)
    f = sf.instantaneous_frequency(np.cos(phase), fs)
    mid = fc + dev * np.cos(2 * np.pi * fm * (n[:-1] + 0.5) / fs)
    assert np.allclose(f, mid, atol=0.05)


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.instantaneous_frequency(np.array([1.0 + 1.0j, 0.0, 1.0]), 10.0)
