"""Podani's richness-difference part of the Jaccard dissimilarity (ADR 0585)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_adds_to_the_jaccard_dissimilarity() -> None:
    rng = np.random.default_rng(585)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = int(np.count_nonzero((x > 0) & (y > 0)))
        b = int(np.count_nonzero((x > 0) & (y == 0)))
        c = int(np.count_nonzero((x == 0) & (y > 0)))
        got = sf.podani_richness_difference(x, y)
        assert got == abs(b - c) / (a + b + c)
        assert sf.podani_richness_difference(y, x) == got
        total = got + sf.podani_replacement(x, y)
        assert total == pytest.approx((b + c) / (a + b + c), rel=1e-15, abs=1e-15)


def test_special_cases() -> None:
    assert sf.podani_richness_difference([1.0, 2.0, 3.0, 0.0], [1e300, 0.0, 0.0, 0.0]) == 2.0 / 3.0
    assert sf.podani_richness_difference([1.0, 0.0], [0.0, 1.0]) == 0.0


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
        sf.podani_richness_difference(x, y)
