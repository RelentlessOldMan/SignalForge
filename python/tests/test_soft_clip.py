"""Cubic soft clipper (ADR 0250)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_odd_monotonic_and_bounded() -> None:
    x = np.arange(-300, 301) / 100
    y = sf.soft_clip(x)
    assert np.array_equal(y, -y[::-1])
    assert np.all(np.diff(y) >= -1e-15)
    assert np.max(np.abs(y)) == 2.0 / 3.0
    assert sf.soft_clip([1.0])[0] == 2.0 / 3.0


def test_only_odd_harmonics() -> None:
    n = np.arange(1024)
    y = sf.soft_clip(0.9 * np.sin(2 * np.pi * 8 * n / 1024))
    s = np.abs(np.fft.fft(y)) / 512
    assert s[24] > 1e-3
    assert max(s[16], s[32]) < 1e-12


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.soft_clip(np.array([0.5 + 0.5j]))
