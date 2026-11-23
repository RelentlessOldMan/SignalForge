"""Podani's nestedness of two presence records (ADR 0588)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(588)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = int(np.count_nonzero((x > 0) & (y > 0)))
        b = int(np.count_nonzero((x > 0) & (y == 0)))
        c = int(np.count_nonzero((x == 0) & (y > 0)))
        got = sf.podani_nestedness(x, y)
        assert got == ((a + abs(b - c)) / (a + b + c) if a else 0.0)
        assert sf.podani_nestedness(y, x) == got
        if a:
            assert got == pytest.approx(1.0 - sf.podani_replacement(x, y), abs=1e-15)


def test_special_cases() -> None:
    assert sf.podani_nestedness([1.0, 2.0, 3.0, 0.0], [1e300, 0.0, 0.0, 0.0]) == 1.0
    assert sf.podani_nestedness([1.0, 0.0, 0.0], [0.0, 1.0, 1.0]) == 0.0


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
        sf.podani_nestedness(x, y)
