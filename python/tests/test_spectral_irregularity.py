"""Spectral irregularity (conventions: Spectra, Spectral irregularity; ADR 0132)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)
P = np.array([3.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])


def test_scaling_the_psd_changes_nothing() -> None:
    want = sf.spectral_irregularity(F, P)
    assert sf.spectral_irregularity(F, 1e-4 * P) == pytest.approx(want, rel=1e-12)


def test_stretching_the_axis_changes_nothing() -> None:
    want = sf.spectral_irregularity(F, P)
    assert sf.spectral_irregularity(1000.0 + 37.5 * F, P) == pytest.approx(want, rel=1e-12)


def test_reversing_the_psd_changes_nothing() -> None:
    want = sf.spectral_irregularity(F, P, band=(0.25, 8.0))
    got = sf.spectral_irregularity(F, P[::-1], band=(1.0, 8.75))
    assert got == pytest.approx(want, rel=1e-12)


def test_uncut_bins_match_jensens_form() -> None:
    want = float(np.sum(np.diff(P) ** 2) / np.sum(P * P))
    assert sf.spectral_irregularity(F, P) == pytest.approx(want, rel=1e-12)
