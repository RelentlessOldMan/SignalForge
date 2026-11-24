"""Hurlbert's niche overlap (ADR 0600)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(600)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        available = rng.uniform(0.5, 4.0, 12)
        x[0] = 1.0
        y[1] = 1.0
        p = x / x.sum()
        q = y / y.sum()
        r = available / available.sum()
        got = sf.hurlbert_overlap(x, y, available)
        assert got == pytest.approx(float(np.sum(p * q / r)), rel=1e-14, abs=1e-15)
        assert sf.hurlbert_overlap(y, x, available) == got
        assert sf.hurlbert_overlap(3.0 * x, y, 0.5 * available) == pytest.approx(
            got, rel=1e-14, abs=1e-15
        )
        assert sf.hurlbert_overlap(available, available, available) == pytest.approx(1.0, abs=1e-14)


def test_special_cases() -> None:
    assert sf.hurlbert_overlap([1.0, 1.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0], [1.0] * 4) == 2.0
    assert sf.hurlbert_overlap([1.0, 0.0], [0.0, 1.0], [1.0, 1.0]) == 0.0
    assert sf.hurlbert_overlap([1e308, 1e308], [1.0, 3.0], [1e308, 1e308]) == 1.0


@pytest.mark.parametrize(
    ("x", "y", "available"),
    [
        ([], [], []),
        ([1.0, 2.0], [1.0], [1.0, 1.0]),
        ([1.0, 2.0], [1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 2.0], [1.0, 1.0]),
        ([1.0, -1.0], [1.0, 2.0], [1.0, 1.0]),
        ([1.0, np.nan], [1.0, 2.0], [1.0, 1.0]),
        ([[1.0, 2.0]], [[1.0, 2.0]], [[1.0, 1.0]]),
        ([1.0, 2.0], [1.0, 2.0], [1.0, 0.0]),
        ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1e300, 5e-324, 1.0]),
        ([1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]),
    ],
)
def test_rejects_bad_arguments(x: list[float], y: list[float], available: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hurlbert_overlap(x, y, available)
