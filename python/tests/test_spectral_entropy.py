"""Spectral entropy (conventions: Spectra, Spectral entropy; ADR 0128)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

P = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])
F = np.arange(10.0)


def test_scaling_the_psd_changes_nothing() -> None:
    want = sf.spectral_entropy(F, P)
    got = sf.spectral_entropy(F, 1e7 * P)
    assert got.entropy == pytest.approx(want.entropy, rel=1e-12)
    assert got.normalized == pytest.approx(want.normalized, rel=1e-12)


def test_stretching_the_axis_scales_the_bandwidth() -> None:
    want = sf.spectral_entropy(F, P)
    got = sf.spectral_entropy(250.0 * F, P)
    assert got.entropy_bandwidth == pytest.approx(250.0 * want.entropy_bandwidth, rel=1e-11)
    assert got.normalized == pytest.approx(want.normalized, rel=1e-11)


def test_tone_over_a_low_floor_is_narrow() -> None:
    p = np.full(1000, 1e-6)
    p[400] = 1.0
    got = sf.spectral_entropy(np.arange(1000.0), p)
    assert got.normalized < 0.005


def test_white_noise_periodogram() -> None:
    n = 200_000
    p = np.random.default_rng(11).exponential(size=n)
    got = sf.spectral_entropy(np.arange(float(n)), p)
    assert got.normalized == pytest.approx(math.exp(np.euler_gamma - 1), rel=0.01)
