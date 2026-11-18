"""Sine wavefolder (ADR 0323)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_in_gives_odd_harmonics_only() -> None:
    n = 1024
    x = 0.9 * np.sin(2 * np.pi * 8 * np.arange(n) / n)
    s = np.abs(np.fft.rfft(sf.sine_fold(x, 3.0)))
    even = s[16::16]
    assert np.max(even) < 1e-9 * np.max(s)
    assert s[24] > 1e-3 * np.max(s)


def test_drive_adds_a_fold_every_two() -> None:
    # A ramp from 0 to 1 turns round (y' changes sign) floor((drive + 1)/2) times.
    x = np.linspace(0, 1, 20001)
    for drive, turns in ((0.9, 0), (1.5, 1), (4.5, 2), (6.5, 3)):
        d = np.diff(sf.sine_fold(x, drive))
        assert int(np.sum(np.diff(np.sign(d)) != 0)) == turns


def test_rejects_a_complex_sample() -> None:
    with pytest.raises(ValueError):
        sf.sine_fold([0.5j], 1.0)
