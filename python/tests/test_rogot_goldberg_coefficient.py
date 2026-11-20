"""The Rogot-Goldberg coefficient (ADR 0467)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_from_zero_to_one() -> None:
    rng = np.random.default_rng(230)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        v = sf.rogot_goldberg_coefficient(t, d)
        assert 0.0 <= v <= 1.0
        assert v == sf.rogot_goldberg_coefficient(d, t)


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    flipped = sf.rogot_goldberg_coefficient(1 - t, 1 - d)
    assert flipped == pytest.approx(sf.rogot_goldberg_coefficient(t, d), rel=1e-15)


def test_rejects_records_both_all_zero() -> None:
    with pytest.raises(ValueError):
        sf.rogot_goldberg_coefficient([0.0, 0.0], [0.0, 0.0])
