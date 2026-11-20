"""The Gower-Legendre coefficient (ADR 0455)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_lies_between_simple_matching_and_one() -> None:
    rng = np.random.default_rng(218)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.gower_legendre_coefficient(t, d)
        s = sf.simple_matching_coefficient(t, d)
        assert v == pytest.approx(2 * s / (1 + s), rel=1e-15)
        assert s <= v <= 1.0


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    assert sf.gower_legendre_coefficient(1 - t, 1 - d) == sf.gower_legendre_coefficient(t, d)


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.gower_legendre_coefficient([1.0, 0.0], [1.0])
