"""Farrow resampler (ADR 0228)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_farrow_delay_reads() -> None:
    rng = np.random.default_rng(6)
    x = rng.standard_normal(30) + 1j * rng.standard_normal(30)
    r = 1.37
    y = sf.farrow_resample(x, r, order=5)
    t = np.arange(y.size) / r
    assert t[-1] <= 29 < (y.size) / r
    # farrow_delay reads sample n at n - delays[n]; read the same positions one at a time
    for k in range(y.size):
        n = int(np.ceil(t[k]))
        d = np.zeros(30)
        d[n] = n - t[k]
        assert abs(sf.farrow_delay(x, d, order=5)[n] - y[k]) < 1e-12


def test_sine_resampled() -> None:
    n = np.arange(400)
    x = np.sin(2 * np.pi * 0.01 * n)
    y = sf.farrow_resample(x, 1.5, order=5)
    t = np.arange(y.size) / 1.5
    inside = (t > 3) & (t < 396)
    assert np.max(np.abs(y[inside] - np.sin(2 * np.pi * 0.01 * t[inside]))) < 1e-6
