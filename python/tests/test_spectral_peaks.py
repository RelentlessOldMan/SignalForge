"""Spectral peaks (conventions: Spectra, Spectral peaks; ADR 0135)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(12.0)
P = np.array([0.5, 3.0, 1.0, 4.0, 4.0, 2.0, 6.0, 0.2, 1.0, 0.3, 2.5, 1.5])


def test_scaling_scales_heights_and_prominences() -> None:
    base = sf.spectral_peaks(F, P)
    scaled = sf.spectral_peaks(F, 8 * P)
    assert [p.index for p in scaled] == [p.index for p in base]
    for a, b in zip(base, scaled, strict=True):
        assert b.height == 8 * a.height
        assert b.prominence == 8 * a.prominence


def test_height_is_at_least_the_prominence() -> None:
    got = sf.spectral_peaks(F, P)
    assert got
    assert all(0 < p.prominence <= p.height for p in got)


def test_threshold_keeps_a_subset() -> None:
    every = sf.spectral_peaks(F, P)
    kept = sf.spectral_peaks(F, P, min_prominence=2.0)
    assert kept == [p for p in every if p.prominence >= 2.0]


def test_tones_in_noise_are_the_most_prominent() -> None:
    rng = np.random.default_rng(135)
    f = np.arange(256.0) * 10
    psd = rng.exponential(1.0, 256)
    psd[[40, 170]] += 100.0
    got = sorted(sf.spectral_peaks(f, psd), key=lambda p: -p.prominence)
    assert sorted(p.index for p in got[:2]) == [40, 170]
    assert sorted(p.frequency for p in got[:2]) == [400.0, 1700.0]


@pytest.mark.parametrize("floor", [-0.5, float("nan"), float("inf")])
def test_bad_floor_is_rejected(floor: float) -> None:
    with pytest.raises(ValueError):
        sf.spectral_peaks(F, P, min_prominence=floor)
