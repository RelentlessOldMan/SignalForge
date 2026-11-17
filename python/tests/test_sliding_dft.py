"""Sliding DFT (ADR 0231)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_equals_fft_of_each_full_window() -> None:
    rng = np.random.default_rng(10)
    x = rng.standard_normal(300) + 1j * rng.standard_normal(300)
    n, k = 16, 5
    s = sf.sliding_dft(x, n, k)
    for i in range(n - 1, 300):
        assert abs(s[i] - np.fft.fft(x[i - n + 1 : i + 1])[k]) < 1e-10
