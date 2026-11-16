"""Spectral slope (conventions: Spectra, Spectral slope; ADR 0127)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

P = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])
F = np.arange(10.0)


@pytest.mark.parametrize("m", [2, 3, 7, 64, 501])
def test_a_sampled_line_gives_the_staircase_slope(m: int) -> None:
    f = np.arange(float(m))
    got = sf.spectral_slope(f, 5.0 + 0.3 * f)
    assert got.slope == pytest.approx(0.3 * (1 - 1 / m**2), rel=1e-11)
    assert got.level == pytest.approx(5.0 + 0.3 * (m - 1) / 2, rel=1e-12)


def test_level_times_width_is_the_band_power() -> None:
    band = (1.2, 7.9)
    got = sf.spectral_slope(F, P, band=band)
    power = sf.spectral_moments(F, P, band=band).power
    assert got.level * (band[1] - band[0]) == pytest.approx(power, rel=1e-12)
    assert got.center == pytest.approx(4.55)


def test_mirroring_negates_the_slope() -> None:
    got, mirrored = sf.spectral_slope(F, P), sf.spectral_slope(F, P[::-1])
    assert mirrored.slope == pytest.approx(-got.slope, rel=1e-12)
    assert mirrored.level == pytest.approx(got.level, rel=1e-12)


def test_shifting_the_axis_changes_only_the_center() -> None:
    want = sf.spectral_slope(F, P)
    got = sf.spectral_slope(F + 1e4, P)
    assert got.center == pytest.approx(want.center + 1e4)
    assert got.level == pytest.approx(want.level, rel=1e-12)
    assert got.slope == pytest.approx(want.slope, rel=1e-8)


def test_db_of_an_exponential_psd() -> None:
    # 10 log10 of 10^(-0.05 f) is -0.5 f dB: a dB line, flattened by the staircase.
    m = 40
    f = np.arange(float(m))
    got = sf.spectral_slope(f, 10 ** (-0.05 * f), db=True)
    assert got.slope == pytest.approx(-0.5 * (1 - 1 / m**2), rel=1e-11)
