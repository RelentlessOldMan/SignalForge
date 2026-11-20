"""Gower's coefficient (ADR 0469)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_at_least_zero() -> None:
    rng = np.random.default_rng(232)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        v = sf.gower_coefficient(t, d)
        assert v >= 0.0
        assert v == sf.gower_coefficient(d, t)


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    assert sf.gower_coefficient(1 - t, 1 - d) == sf.gower_coefficient(t, d)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.gower_coefficient([1.0, 1.0], [1.0, 0.0])
