"""Temporal centroid and spread (conventions: Temporal centroid; ADR 0147)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

X = np.random.default_rng(147).standard_normal(64) * np.hanning(64)


def test_delay_shifts_the_centroid_only() -> None:
    a = sf.temporal_centroid(X, 1000.0)
    b = sf.temporal_centroid(np.concatenate((np.zeros(10), X)), 1000.0)
    assert b.centroid == pytest.approx(a.centroid + 10 / 1000.0, rel=1e-12)
    assert b.spread == pytest.approx(a.spread, rel=1e-12)


def test_scaling_leaves_it_unchanged() -> None:
    a = sf.temporal_centroid(X, 1000.0)
    b = sf.temporal_centroid((2 - 3j) * X, 1000.0)
    assert (b.centroid, b.spread) == pytest.approx((a.centroid, a.spread), rel=1e-12)
