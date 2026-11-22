"""Pianka's niche overlap (ADR 0571)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition_on_shares() -> None:
    rng = np.random.default_rng(571)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 9)
        y = rng.uniform(0.0, 4.0, 9)
        p = x / np.sum(x)
        q = y / np.sum(y)
        want = float(np.sum(p * q) / np.sqrt(np.sum(p * p) * np.sum(q * q)))
        assert sf.pianka_overlap(x, y) == pytest.approx(want, rel=1e-13)
        assert sf.pianka_overlap(y, x) == pytest.approx(want, rel=1e-15)


def test_bounds_and_scale() -> None:
    assert sf.pianka_overlap([1.0, 2.0, 3.0], [3e-200, 6e-200, 9e-200]) == pytest.approx(
        1.0, rel=1e-15
    )
    assert sf.pianka_overlap([1.0, 0.0, 0.0], [0.0, 2.0, 5.0]) == 0.0
    assert 0.0 < sf.pianka_overlap([1e6, 1.0], [1.0, 1e6]) < 1e-5


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
        sf.pianka_overlap(x, y)
