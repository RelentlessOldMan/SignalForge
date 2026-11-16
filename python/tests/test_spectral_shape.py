"""Spectral skewness and kurtosis (conventions: Spectra, Spectral skewness and kurtosis; ADR
0126)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

P = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])
F = np.arange(10.0)


def test_mirroring_flips_the_skewness() -> None:
    got = sf.spectral_shape(F, P)
    mirrored = sf.spectral_shape(F, P[::-1])
    assert mirrored.skewness == pytest.approx(-got.skewness, rel=1e-11)
    assert mirrored.kurtosis == pytest.approx(got.kurtosis, rel=1e-11)


def test_axis_shift_and_stretch_change_nothing() -> None:
    want = sf.spectral_shape(F, P)
    for shift, stretch in [(1e3, 1.0), (-50.0, 0.01), (7.0, 250.0)]:
        got = sf.spectral_shape(shift + stretch * F, P)
        assert got.skewness == pytest.approx(want.skewness, rel=1e-9)
        assert got.kurtosis == pytest.approx(want.kurtosis, rel=1e-9)


def test_scaling_changes_nothing() -> None:
    want = sf.spectral_shape(F, P)
    got = sf.spectral_shape(F, 1e6 * P)
    assert got.skewness == pytest.approx(want.skewness, rel=1e-12)
    assert got.kurtosis == pytest.approx(want.kurtosis, rel=1e-12)


def test_gaussian_psd() -> None:
    f = np.arange(-400.0, 401.0)
    sigma = 40.0
    got = sf.spectral_shape(f, np.exp(-(f**2) / (2 * sigma**2)))
    assert got.skewness == pytest.approx(0.0, abs=1e-12)
    # A step density adds a bin's own uniform spread: m2 = s² + 1/12, m4 = 3s⁴ + s²/2 + 1/80.
    m2, m4 = sigma**2 + 1 / 12, 3 * sigma**4 + sigma**2 / 2 + 1 / 80
    assert got.kurtosis == pytest.approx(m4 / m2**2, rel=1e-6)


def test_flat_band_is_uniform() -> None:
    got = sf.spectral_shape(F, np.ones(10), band=(1.3, 6.1))
    assert got.skewness == pytest.approx(0.0, abs=1e-12)
    assert got.kurtosis == pytest.approx(9 / 5, rel=1e-12)
