"""Farrow variable delay (ADR 0226)."""

from __future__ import annotations

import math

import numpy as np

import signalforge as sf


def test_matches_lagrange_fir_per_sample() -> None:
    rng = np.random.default_rng(5)
    x = rng.standard_normal(40) + 1j * rng.standard_normal(40)
    d = 2.0 + 3.0 * rng.random(40)
    for order in (1, 2, 3, 4, 5):
        y = sf.farrow_delay(x, d, order=order)
        half = (order - 1) / 2
        for i in range(40):
            q = i - d[i] - half
            b = math.floor(q)
            u = q - b + half
            h = sf.lagrange_fir(order - u, order)
            want = sum(h[k] * x[b + order - k] for k in range(order + 1) if 0 <= b + order - k < 40)
            assert abs(y[i] - want) < 1e-11


def test_constant_delay_matches_convolution() -> None:
    x = np.cos(0.3 * np.arange(30))
    y = sf.farrow_delay(x, np.full(30, 1.25))
    h = sf.lagrange_fir(1.25, 3)
    assert np.allclose(y[3:], np.convolve(x, h)[3:30], atol=1e-12)
