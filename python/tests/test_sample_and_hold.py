"""Sample-and-hold (ADR 0245)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_repeat_of_decimated() -> None:
    x = np.random.default_rng(20).standard_normal(100)
    y = sf.sample_and_hold(x, 7)
    assert np.array_equal(y, np.repeat(x[::7], 7)[:100])


def test_complex_stays_complex() -> None:
    y = sf.sample_and_hold(np.array([1 + 2j, 3 - 4j, 5j]), 2, offset=1)
    assert np.array_equal(y, np.array([0, 3 - 4j, 3 - 4j]))
