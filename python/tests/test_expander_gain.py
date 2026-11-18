"""Downward-expander gain computer (ADR 0256)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_curve_and_slope_are_continuous() -> None:
    x = np.linspace(-90, 0, 90001)
    g = sf.expander_gain(x, -45.0, 3.0, knee_db=10.0)
    assert np.max(np.abs(np.diff(g))) < 3e-3
    slope = np.diff(g) / np.diff(x)
    assert np.max(np.abs(np.diff(slope))) < 1e-3
    assert np.all(g <= 0)


def test_mirrors_the_compressor_for_ratio_two() -> None:
    x = np.arange(-60, 1, 0.25)
    e = sf.expander_gain(x, -30.0, 2.0)
    assert np.array_equal(e[x >= -30], np.zeros(np.count_nonzero(x >= -30)))
    assert np.array_equal(e[x < -30], x[x < -30] + 30)
