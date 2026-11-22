"""Morisita's overlap of two count records (ADR 0581)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(581)
    for _ in range(20):
        x = rng.integers(0, 6, 12).astype(float)
        y = rng.integers(0, 6, 12).astype(float)
        x[0] = 3.0
        y[1] = 3.0
        lx = float(np.sum(x * (x - 1)) / (x.sum() * (x.sum() - 1)))
        ly = float(np.sum(y * (y - 1)) / (y.sum() * (y.sum() - 1)))
        want = 2.0 * float(np.dot(x, y)) / ((lx + ly) * x.sum() * y.sum())
        got = sf.morisita_overlap(x, y)
        assert got == pytest.approx(want, rel=1e-13)
        assert sf.morisita_overlap(y, x) == pytest.approx(got, rel=1e-15)
        assert got >= 0.0


def test_special_cases() -> None:
    assert sf.morisita_overlap([5.0, 5.0], [5.0, 5.0]) == 1.125
    assert sf.morisita_overlap([3.0, 1.0], [1.0, 3.0]) == 0.75
    assert sf.morisita_overlap([2.0, 0.0], [0.0, 2.0]) == 0.0


@pytest.mark.parametrize(
    ("x", "y"),
    [
        ([], []),
        ([2.0, 2.0], [2.0]),
        ([1.0, 0.0], [1.0, 2.0]),
        ([2.0, -1.0], [1.0, 2.0]),
        ([2.0, 0.5], [1.0, 2.0]),
        ([2.0, np.nan], [1.0, 2.0]),
        ([1.0, 1.0], [1.0, 1.0]),
        ([10_000_001.0, 0.0], [1.0, 2.0]),
        ([[1.0, 2.0]], [[1.0, 2.0]]),
    ],
)
def test_rejects_bad_arguments(x: list[float], y: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.morisita_overlap(x, y)
