"""Spectral rolloff (conventions: Spectra, Spectral rolloff; ADR 0124)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)


@pytest.mark.parametrize("q", [0.01, 0.1, 0.25, 0.5, 0.85, 0.95, 1.0])
def test_flat_psd_gives_the_linear_share(q: float) -> None:
    assert sf.spectral_rolloff(F, np.ones(10), q) == pytest.approx(-0.5 + q * 10, abs=1e-12)


def test_scaling_changes_nothing() -> None:
    p = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.0])
    want = sf.spectral_rolloff(F, p, 0.7)
    for k in (1e-9, 3.0, 1e9):
        assert sf.spectral_rolloff(F, k * p, 0.7) == pytest.approx(want, rel=1e-12)


def test_rolloff_rises_with_the_fraction() -> None:
    p = np.random.default_rng(5).random(64) * (np.arange(64) % 3 != 0)
    got = [sf.spectral_rolloff(np.arange(64.0), p, q) for q in np.linspace(0.01, 1.0, 100)]
    assert all(b >= a for a, b in itertools.pairwise(got))


def test_symmetric_psd_halves_at_its_centre() -> None:
    p = np.array([1.0, 2.0, 5.0, 2.0, 1.0])
    assert sf.spectral_rolloff([10.0, 11.0, 12.0, 13.0, 14.0], p, 0.5) == pytest.approx(12.0)


def test_band_cuts_bins() -> None:
    assert sf.spectral_rolloff(F, np.ones(10), 0.5, band=(2.25, 3.75)) == pytest.approx(3.0)
