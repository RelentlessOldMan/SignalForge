"""Horn's information overlap (ADR 0574)."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf


def _xlnx(v: NDArray[np.float64]) -> float:
    w = v[v > 0]
    return float(np.sum(w * np.log(w)))


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(574)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 9)
        y = rng.uniform(0.0, 9.0, 9)
        sx, sy = np.sum(x), np.sum(y)
        den = (sx + sy) * np.log(sx + sy) - sx * np.log(sx) - sy * np.log(sy)
        want = (_xlnx(x + y) - _xlnx(x) - _xlnx(y)) / den
        assert sf.horn_overlap(x, y) == pytest.approx(want, rel=1e-12)
        assert sf.horn_overlap(y, x) == pytest.approx(want, rel=1e-15)
        assert sf.horn_overlap(x * 1e5, y * 1e5) == pytest.approx(want, rel=1e-13)


def test_bounds() -> None:
    assert sf.horn_overlap([1.0, 2.0, 3.0], [3e-5, 6e-5, 9e-5]) == pytest.approx(1.0, rel=1e-14)
    assert sf.horn_overlap([1.0, 0.0, 0.0], [0.0, 2.0, 5.0]) == 0.0
    assert 0.0 < sf.horn_overlap([1e6, 1.0], [1.0, 1e6]) < 1e-4


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
        sf.horn_overlap(x, y)
