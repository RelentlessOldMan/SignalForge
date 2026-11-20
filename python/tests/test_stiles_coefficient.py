"""Stiles' coefficient (ADR 0451)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_unchanged_when_a_record_is_flipped() -> None:
    rng = np.random.default_rng(214)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = d[:2] = [1.0, 0.0]
        v = sf.stiles_coefficient(t, d)
        assert v == sf.stiles_coefficient(d, t)
        assert sf.stiles_coefficient(t, 1 - d) == pytest.approx(v, rel=1e-14, abs=1e-14)


def test_is_log10_of_yates_chi_square_over_n() -> None:
    t = np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    d = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    tp, fn, fp, tn = 3, 2, 1, 3
    n = 9
    chi = n * (abs(tp * tn - fn * fp) - n / 2) ** 2 / (5 * 4 * 4 * 5)
    assert sf.stiles_coefficient(t, d) == pytest.approx(math.log10(chi), rel=1e-14)


def test_rejects_a_cross_difference_of_half_n() -> None:
    with pytest.raises(ValueError):
        sf.stiles_coefficient([1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0])
