"""The Hamming distance (ADR 0421)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_counts_the_flipped_bits() -> None:
    rng = np.random.default_rng(177)
    bits = rng.integers(0, 2, 100)
    flipped = bits.copy()
    flipped[[3, 17, 50, 99]] ^= 1
    assert sf.hamming_distance(bits, flipped) == 4


def test_obeys_the_triangle_inequality() -> None:
    rng = np.random.default_rng(178)
    for _ in range(20):
        x, y, z = rng.integers(0, 3, size=(3, 12)).astype(float)
        d = sf.hamming_distance
        assert d(x, z) <= d(x, y) + d(y, z)


def test_rejects_nan() -> None:
    with pytest.raises(ValueError):
        sf.hamming_distance([np.nan], [np.nan])
