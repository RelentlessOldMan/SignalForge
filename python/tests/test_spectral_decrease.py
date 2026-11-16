"""Spectral decrease (conventions: Spectra, Spectral decrease; ADR 0130)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)
P = np.array([3.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.2])


def test_scaling_the_psd_changes_nothing() -> None:
    want = sf.spectral_decrease(F, P)
    assert sf.spectral_decrease(F, 1e-4 * P) == pytest.approx(want, rel=1e-12)


def test_stretching_the_axis_changes_nothing() -> None:
    want = sf.spectral_decrease(F, P)
    assert sf.spectral_decrease(1000.0 + 37.5 * F, P) == pytest.approx(want, rel=1e-12)


def test_uncut_bins_match_the_library_form() -> None:
    k = np.arange(1, P.size)
    want = float(np.sum((P[1:] - P[0]) / k) / np.sum(P[1:]))
    assert sf.spectral_decrease(F, P) == pytest.approx(want, rel=1e-12)
