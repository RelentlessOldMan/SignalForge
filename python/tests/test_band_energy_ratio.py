"""Band energy ratio (conventions: Spectra, Band energy ratio; ADR 0134)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)
P = np.array([3.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.1, 4.0, 1.0, 0.2])


def test_low_and_high_add_to_the_channel_power() -> None:
    got = sf.band_energy_ratio(F, P, 3.7, band=(0.25, 8.6))
    assert got.low + got.high == pytest.approx(sf.channel_power(F, P, 0.25, 8.6), rel=1e-12)


def test_mirroring_inverts_the_ratio() -> None:
    there = sf.band_energy_ratio(F, P, 4.5)
    back = sf.band_energy_ratio(F, P[::-1], 4.5)
    assert back.ratio == pytest.approx(1 / there.ratio, rel=1e-12)
    assert back.ratio_db == pytest.approx(-there.ratio_db, rel=1e-12)


def test_no_low_power_is_infinite() -> None:
    got = sf.band_energy_ratio(F, np.where(F < 5, 0.0, P), 4.5)
    assert got.low == 0
    assert got.ratio == math.inf
    assert got.ratio_db == math.inf


def test_no_high_power_is_zero() -> None:
    got = sf.band_energy_ratio(F, np.where(F < 5, P, 0.0), 4.5)
    assert got.ratio == 0
    assert got.ratio_db == -math.inf
