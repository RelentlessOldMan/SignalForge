"""Running median filter (ADR 0234)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_interior_matches_numpy_median() -> None:
    rng = np.random.default_rng(11)
    x = rng.standard_normal(200)
    y = sf.median_filter(x, 9)
    for n in range(4, 196):
        assert y[n] == np.median(x[n - 4 : n + 5])
    assert y[0] == x[0] and y[-1] == x[-1]
