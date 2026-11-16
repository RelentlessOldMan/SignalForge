"""Spectral centroid and RMS bandwidth (conventions: Spectra, Spectral centroid and RMS
bandwidth; ADR 0121)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize(("lo", "hi"), [(10, 30), (0, 99), (40, 41)])
def test_rectangle_is_width_over_root_twelve(lo: int, hi: int) -> None:
    f = np.arange(100, dtype=np.float64) * 0.5
    p = np.where((np.arange(100) >= lo) & (np.arange(100) <= hi), 3.0, 0.0)
    r = sf.spectral_moments(f, p)
    width = (hi - lo + 1) * 0.5
    assert r.power == pytest.approx(3 * width, rel=1e-12)
    assert r.centroid == pytest.approx((f[lo] + f[hi]) / 2, rel=1e-12)
    assert r.rms_bandwidth == pytest.approx(width / math.sqrt(12), rel=1e-12)


def test_cut_band_on_a_flat_psd() -> None:
    f = np.arange(64, dtype=np.float64)
    r = sf.spectral_moments(f, np.ones(64), band=(10.3, 40.8))
    assert r.power == pytest.approx(30.5, rel=1e-12)
    assert r.centroid == pytest.approx((10.3 + 40.8) / 2, rel=1e-12)
    assert r.rms_bandwidth == pytest.approx(30.5 / math.sqrt(12), rel=1e-12)


def test_gaussian_psd_gives_its_sigma() -> None:
    f = np.linspace(-50, 50, 20001)
    sigma = 4.0
    p = np.exp(-((f - 1.25) ** 2) / (2 * sigma**2))
    r = sf.spectral_moments(f, p)
    assert r.centroid == pytest.approx(1.25, abs=1e-9)
    # the step density adds delta^2 / 12 to the variance
    delta = f[1] - f[0]
    assert r.rms_bandwidth == pytest.approx(math.sqrt(sigma**2 + delta**2 / 12), rel=1e-9)


def test_shifting_the_axis_shifts_only_the_centroid() -> None:
    rng = np.random.default_rng(121)
    f = np.arange(80, dtype=np.float64)
    p = rng.uniform(0, 1, size=80)
    a = sf.spectral_moments(f, p)
    b = sf.spectral_moments(f + 1e6, p)
    assert b.centroid - 1e6 == pytest.approx(a.centroid, abs=1e-8)
    assert b.rms_bandwidth == pytest.approx(a.rms_bandwidth, rel=1e-9)
    assert b.power == pytest.approx(a.power, rel=1e-12)


def test_power_matches_channel_power() -> None:
    rng = np.random.default_rng(1210)
    f = np.arange(40, dtype=np.float64)
    p = rng.uniform(0, 1, size=40)
    band = (3.7, 22.2)
    assert sf.spectral_moments(f, p, band=band).power == pytest.approx(
        sf.channel_power(f, p, *band), rel=1e-12
    )
