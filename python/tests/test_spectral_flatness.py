"""Spectral flatness (conventions: Spectra, Spectral flatness; ADR 0120)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize(("x", "y", "count"), [(1.0, 10.0, 100), (0.5, 2.0, 37), (3.0, 1e-3, 250)])
def test_two_level_closed_form(x: float, y: float, count: int) -> None:
    n = 1000
    psd = np.full(n, y)
    psd[:count] = x
    a = count / n
    want = x**a * y ** (1 - a) / (a * x + (1 - a) * y)
    r = sf.spectral_flatness(np.arange(n, dtype=np.float64), psd)
    assert r.flatness == pytest.approx(want, rel=1e-12)
    assert r.flatness_db == pytest.approx(10 * math.log10(want), abs=1e-10)


def test_a_tone_is_far_from_flat() -> None:
    n = 4096
    x = np.cos(2 * np.pi * 200 * np.arange(n) / n) + 1e-6 * np.random.default_rng(120).normal(
        size=n
    )
    d = sf.welch_psd(x, 1.0, nperseg=n)
    assert sf.spectral_flatness(d.frequencies, d.psd).flatness < 1e-6


def test_white_noise_is_nearly_flat() -> None:
    # a periodogram bin of white noise is exponential, so E ln d = ln E d - Euler's gamma
    rng = np.random.default_rng(1200)
    x = rng.normal(size=1 << 16) + 1j * rng.normal(size=1 << 16)
    d = sf.welch_psd(x, 1.0, nperseg=x.size, window="rectangular")
    assert sf.spectral_flatness(d.frequencies, d.psd).flatness == pytest.approx(
        math.exp(-0.5772156649), rel=1e-2
    )


def test_scaling_the_psd_leaves_the_flatness() -> None:
    rng = np.random.default_rng(3)
    f = np.arange(64, dtype=np.float64)
    p = rng.uniform(0.1, 2.0, size=64)
    a = sf.spectral_flatness(f, p, band=(10.3, 40.8))
    b = sf.spectral_flatness(f, 1e6 * p, band=(10.3, 40.8))
    assert b.flatness == pytest.approx(a.flatness, rel=1e-12)
    assert b.arithmetic_mean == pytest.approx(1e6 * a.arithmetic_mean, rel=1e-12)


def test_flatness_is_at_most_one() -> None:
    rng = np.random.default_rng(4)
    f = np.arange(50, dtype=np.float64)
    for _ in range(20):
        r = sf.spectral_flatness(f, rng.uniform(0, 1, size=50))
        assert 0 <= r.flatness <= 1 + 1e-15
