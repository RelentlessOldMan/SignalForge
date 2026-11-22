"""Whittaker's beta of two records (ADR 0575)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(575)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        sx = int(np.count_nonzero(x))
        sy = int(np.count_nonzero(y))
        union = int(np.count_nonzero((x > 0) | (y > 0)))
        want = 2.0 * union / (sx + sy) - 1.0
        assert sf.whittaker_beta(x, y) == pytest.approx(want, rel=1e-15, abs=1e-15)
        assert sf.whittaker_beta(y, x) == sf.whittaker_beta(x, y)
        shared = int(np.count_nonzero((x > 0) & (y > 0)))
        assert sf.whittaker_beta(x, y) == pytest.approx(1.0 - 2.0 * shared / (sx + sy))


def test_ignores_the_amounts() -> None:
    assert sf.whittaker_beta([1.0, 2.0, 3.0], [1e300, 1e-300, 7.0]) == 0.0
    assert sf.whittaker_beta([1.0, 0.0], [0.0, 1.0]) == 1.0


@pytest.mark.parametrize(
    ("x", "y"),
    [
        ([], []),
        ([1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 2.0]),
        ([1.0, -1.0], [1.0, 2.0]),
        ([1.0, np.nan], [1.0, 2.0]),
        ([[1.0, 2.0]], [[1.0, 2.0]]),
    ],
)
def test_rejects_bad_arguments(x: list[float], y: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.whittaker_beta(x, y)
