"""Tremolo (ADR 0261)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_gain_swings_between_one_and_one_minus_depth() -> None:
    y = sf.tremolo(np.ones(9600), 5.0, 0.6, 48000.0)
    assert abs(np.max(y) - 1) < 1e-15
    assert abs(np.min(y) - 0.4) < 1e-12
    assert np.all(y > 0)


def test_sidebands_at_the_rate() -> None:
    fs, n = 8000.0, 8000
    x = sf.tone(fs, n, 1000.0, complex=False)
    y = np.real(sf.tremolo(x, 50.0, 1.0, fs))
    s = np.abs(np.fft.rfft(y)) / (n / 2)
    assert abs(s[1000] - 0.5) < 1e-9
    assert abs(s[950] - 0.25) < 1e-9 and abs(s[1050] - 0.25) < 1e-9
