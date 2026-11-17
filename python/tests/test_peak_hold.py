"""Peak hold (ADR 0243)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_never_below_the_input() -> None:
    x = np.random.default_rng(18).standard_normal(500)
    y = sf.peak_hold(x, 10, 0.9)
    assert np.all(y >= np.abs(x))


def test_holds_then_decays() -> None:
    x = np.zeros(30)
    x[5] = 2.0
    y = sf.peak_hold(x, 7, 0.5)
    assert np.all(y[5:13] == 2.0)
    assert y[13] == 1.0
