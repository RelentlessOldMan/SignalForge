"""Spectral flux (conventions: Spectra, Spectral flux; ADR 0129)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)
A = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])
B = np.array([1.0, 0.5, 2.0, 4.0, 1.0, 0.0, 2.0, 3.0, 0.1, 0.7])


def test_unrectified_is_symmetric() -> None:
    there = sf.spectral_flux(F, A, B, rectify=False)
    back = sf.spectral_flux(F, B, A, rectify=False)
    assert there == pytest.approx(back, rel=1e-13)


def test_rises_and_falls_add_in_squares() -> None:
    up = sf.spectral_flux(F, A, B)
    down = sf.spectral_flux(F, B, A)
    both = sf.spectral_flux(F, A, B, rectify=False)
    assert up**2 + down**2 == pytest.approx(both**2, rel=1e-12)


def test_scaling_a_frame_changes_nothing_normalized() -> None:
    want = sf.spectral_flux(F, A, B, band=(1.25, 8.0))
    got = sf.spectral_flux(F, 3e5 * A, 0.01 * B, band=(1.25, 8.0))
    assert got == pytest.approx(want, rel=1e-12)


def test_lengths_must_match() -> None:
    with pytest.raises(ValueError):
        sf.spectral_flux(F, A, B[:-1])
