"""Harmonic centroid and spread (conventions: Spectra, Harmonic centroid; ADR 0145)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

TONES = np.array([101.0, 199.0, 302.0, 405.0, 150.0])
HEIGHTS = np.array([5.0, 3.0, 2.0, 1.0, 7.0])
ORDERS = np.array([1, 2, 3, 4, 0])


def test_scaling_heights_leaves_it_unchanged() -> None:
    a = sf.harmonic_centroid(TONES, HEIGHTS, ORDERS)
    b = sf.harmonic_centroid(TONES, 6.0 * HEIGHTS, ORDERS)
    assert (b.centroid, b.spread) == pytest.approx((a.centroid, a.spread), rel=1e-12)


def test_scaling_frequencies_scales_both() -> None:
    a = sf.harmonic_centroid(TONES, HEIGHTS, ORDERS)
    b = sf.harmonic_centroid(2.5 * TONES, HEIGHTS, ORDERS)
    assert (b.centroid, b.spread) == pytest.approx((2.5 * a.centroid, 2.5 * a.spread), rel=1e-12)
