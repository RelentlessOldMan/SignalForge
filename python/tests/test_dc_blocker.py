"""DC blocker (ADR 0236)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_removes_an_offset_and_keeps_a_tone() -> None:
    n = np.arange(20000)
    tone = np.sin(2 * np.pi * 0.05 * n)
    y = sf.dc_blocker(tone + 3.0, 0.995)
    tail = y[10000:]
    assert abs(np.mean(tail)) < 1e-3
    assert abs(np.sqrt(np.mean(tail**2)) - np.sqrt(0.5)) < 5e-3


def test_matches_the_transfer_function() -> None:
    x = np.array([0.5, -1.0, 2.0, 0.25, 1.5, -0.75])
    p = 0.9
    y = np.zeros_like(x)
    for i in range(x.size):
        y[i] = x[i] - (x[i - 1] if i else 0) + p * (y[i - 1] if i else 0)
    assert np.allclose(sf.dc_blocker(x, p), y, rtol=0, atol=1e-15)
