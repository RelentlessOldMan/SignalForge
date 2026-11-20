"""The Benini coefficient (ADR 0465)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_at_most_one() -> None:
    rng = np.random.default_rng(228)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        v = sf.benini_coefficient(t, d)
        assert v <= 1.0
        assert v == sf.benini_coefficient(d, t)


def test_is_one_when_the_ones_nest() -> None:
    t = np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0])
    d = np.array([1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    assert sf.benini_coefficient(t, d) == 1.0
    twice = sf.benini_coefficient(np.tile(t, 3), np.tile(d, 3))
    assert twice == 1.0


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.benini_coefficient([1.0, 0.0], [0.0, 0.0])
