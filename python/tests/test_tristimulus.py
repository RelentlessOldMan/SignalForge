"""Tristimulus (conventions: Spectra, Tristimulus; ADR 0142)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

HEIGHTS = np.array([5.0, 3.0, 2.0, 1.0, 0.5, 0.25, 7.0])
ORDERS = np.array([1, 2, 3, 4, 5, 9, 0])


def test_scaling_heights_leaves_it_unchanged() -> None:
    a = sf.tristimulus(HEIGHTS, ORDERS)
    b = sf.tristimulus(6.0 * HEIGHTS, ORDERS)
    assert (b.first, b.second, b.third) == pytest.approx((a.first, a.second, a.third), rel=1e-12)


def test_shares_sum_to_one() -> None:
    a = sf.tristimulus(HEIGHTS, ORDERS)
    assert a.first + a.second + a.third == pytest.approx(1.0, rel=1e-15)


def test_sawtooth() -> None:
    m = np.arange(1, 11)
    got = sf.tristimulus(1.0 / m**2, m)
    total = sum(1 / k for k in range(1, 11))
    assert got.first == pytest.approx(1 / total, rel=1e-12)
    assert got.second == pytest.approx((1 / 2 + 1 / 3 + 1 / 4) / total, rel=1e-12)
    assert got.third == pytest.approx(sum(1 / k for k in range(5, 11)) / total, rel=1e-12)
