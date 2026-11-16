"""Spectral contrast (conventions: Spectra, Spectral contrast; ADR 0133)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)
P = np.array([3.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.1, 4.0, 1.0, 0.2])


def test_scaling_scales_peak_and_valley() -> None:
    want = sf.spectral_contrast(F, P, band=(0.25, 8.6))
    got = sf.spectral_contrast(F, 1e3 * P, band=(0.25, 8.6))
    assert got.peak == pytest.approx(1e3 * want.peak, rel=1e-12)
    assert got.valley == pytest.approx(1e3 * want.valley, rel=1e-12)
    assert got.contrast_db == pytest.approx(want.contrast_db, rel=1e-12)


def test_half_split_gives_the_mean() -> None:
    got = sf.spectral_contrast(F, P, fraction=0.5)
    assert (got.peak + got.valley) / 2 == pytest.approx(float(np.mean(P)), rel=1e-12)


def test_zero_valley_is_infinite() -> None:
    got = sf.spectral_contrast(F, np.where(P < 0.5, 0.0, P))
    assert got.valley == 0
    assert got.contrast_db == math.inf


def test_tone_over_a_floor() -> None:
    p = np.full(1000, 1e-4)
    p[300:310] = 1.0
    got = sf.spectral_contrast(np.arange(1000.0), p, fraction=0.01)
    assert got.contrast_db == pytest.approx(40.0, rel=1e-12)
