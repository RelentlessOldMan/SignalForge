"""Goertzel (ADR 0224)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_equals_fft_on_bins() -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(64) + 1j * rng.standard_normal(64)
    k = np.arange(64)
    assert np.allclose(sf.goertzel(x, 64.0, k), np.fft.fft(x), atol=1e-11)


def test_equals_direct_dtft_off_bin() -> None:
    rng = np.random.default_rng(4)
    x = rng.standard_normal(50)
    f = np.array([0.37, 3.1, 11.9, -7.25])
    n = np.arange(50)
    direct = np.exp(-2j * np.pi * np.outer(f, n) / 25.0) @ x
    assert np.allclose(sf.goertzel(x, 25.0, f), direct, atol=1e-11)
