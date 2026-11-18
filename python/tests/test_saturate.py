"""Tanh saturator (ADR 0259)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_odd_monotonic_and_bounded() -> None:
    x = np.arange(-500, 501) / 100
    y = sf.saturate(x, 3.0)
    assert np.all(np.diff(y) > 0)
    assert np.allclose(y, -y[::-1], rtol=0, atol=1e-15)
    assert np.max(np.abs(y)) < 1 / np.tanh(3.0)


def test_only_odd_harmonics() -> None:
    n = np.arange(1000)
    y = sf.saturate(np.sin(2 * np.pi * 10 * n / 1000), 2.0)
    s = np.abs(np.fft.rfft(y)) / 500
    assert s[30] > 1e-2
    assert s[20] < 1e-12 and s[40] < 1e-12


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.saturate(np.array([1j]), 1.0)
