"""Spectral variation (conventions: Spectra, Spectral variation; ADR 0131)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)
A = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])
B = np.array([1.0, 0.5, 2.0, 4.0, 1.0, 0.0, 2.0, 3.0, 0.1, 0.7])


def test_swapping_the_frames_changes_nothing() -> None:
    want = sf.spectral_variation(F, A, B)
    assert sf.spectral_variation(F, B, A) == pytest.approx(want, rel=1e-13)


def test_scaling_a_frame_changes_nothing() -> None:
    want = sf.spectral_variation(F, A, B, band=(1.25, 8.0))
    got = sf.spectral_variation(F, 3e5 * A, 0.01 * B, band=(1.25, 8.0))
    assert got == pytest.approx(want, rel=1e-12)


def test_random_frames_stay_in_range() -> None:
    rng = np.random.default_rng(5)
    for _ in range(50):
        v = sf.spectral_variation(F, rng.exponential(size=10), rng.exponential(size=10))
        assert 0.0 <= v <= 1.0
