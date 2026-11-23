"""The balanced-variation part of the Bray-Curtis dissimilarity (ADR 0582)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(582)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = float(np.minimum(x, y).sum())
        least = min(float(x.sum()) - a, float(y.sum()) - a)
        want = least / (a + least)
        got = sf.bray_curtis_balanced(x, y)
        assert got == pytest.approx(want, rel=1e-13, abs=1e-15)
        assert sf.bray_curtis_balanced(y, x) == got
        assert 0.0 <= got <= 1.0


def test_special_cases() -> None:
    assert sf.bray_curtis_balanced([1.5e308, 1.5e308, 0.0], [1.5e308, 0.0, 1.5e308]) == 0.5
    assert sf.bray_curtis_balanced([1.0, 0.0], [0.0, 1.0]) == 1.0
    assert sf.bray_curtis_balanced([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == 0.0


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
        sf.bray_curtis_balanced(x, y)
