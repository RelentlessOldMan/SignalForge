"""Downward expander (ADR 0258)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_loud_signal_untouched() -> None:
    n = np.arange(2000)
    x = 2 + np.sin(2 * np.pi * n / 40)
    assert np.array_equal(sf.expand(x, 0.0, 4.0, 0.5, 0.9), x)


def test_quiet_tone_pushed_down() -> None:
    n = np.arange(20000)
    x = 0.1 * np.sin(2 * np.pi * n / 40)
    y = sf.expand(x, -10.0, 2.0, 0.0, 0.9999)
    peak_db = 20 * np.log10(np.max(np.abs(y[10000:])))
    assert abs(peak_db - (-10 + 2 * (-20 + 10))) < 0.05
