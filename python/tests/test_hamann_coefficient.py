"""The Hamann coefficient (ADR 0432)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_twice_simple_matching_less_one() -> None:
    rng = np.random.default_rng(192)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        want = 2 * sf.simple_matching_coefficient(t, d) - 1
        assert sf.hamann_coefficient(t, d) == pytest.approx(want, rel=1e-14, abs=1e-15)


def test_flipping_one_record_negates_it() -> None:
    rng = np.random.default_rng(193)
    t = (rng.random(30) < 0.5).astype(float)
    d = (rng.random(30) < 0.5).astype(float)
    assert sf.hamann_coefficient(t, 1 - d) == -sf.hamann_coefficient(t, d)


def test_rejects_an_empty_record() -> None:
    with pytest.raises(ValueError):
        sf.hamann_coefficient([], [])
