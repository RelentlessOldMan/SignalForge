"""De-esser (ADR 0286)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_sibilance_is_turned_down_and_a_low_tone_is_not() -> None:
    fs = 48000.0
    n = np.arange(9600)
    low = 0.5 * np.sin(2 * np.pi * 200.0 * n / fs)
    hiss = 0.5 * np.sin(2 * np.pi * 7000.0 * n / fs)
    args = (7000.0, 2.0, -20.0, 8.0, 0.9, 0.999, fs)
    y_low = sf.de_esser(low, *args)
    y_hiss = sf.de_esser(hiss, *args)
    tail = slice(4800, None)
    assert np.max(np.abs(y_low[tail])) == pytest.approx(0.5, rel=1e-3)
    assert np.max(np.abs(y_hiss[tail])) < 0.2


def test_is_duck_keyed_on_the_unity_band() -> None:
    rng = np.random.default_rng(52)
    x = rng.standard_normal(500)
    key = sf.svf(x, 0.2, 3.0, 1.0, output="bandpass") * (1 / 3.0)
    want = sf.duck(x, np.real(key), -6.0, 3.0, 0.3, 0.9)
    assert np.array_equal(sf.de_esser(x, 0.2, 3.0, -6.0, 3.0, 0.3, 0.9, 1.0), want)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.de_esser([1j], 1.0, 1.0, 0.0, 2.0, 0.5, 0.5, 8.0)
