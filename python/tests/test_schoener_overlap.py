"""Schoener's overlap of two records (ADR 0598)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(598)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        p = x / x.sum()
        q = y / y.sum()
        got = sf.schoener_overlap(x, y)
        assert got == pytest.approx(1.0 - 0.5 * float(np.abs(p - q).sum()), abs=1e-14)
        assert got == pytest.approx(1.0 - sf.bray_curtis(p, q), abs=1e-14)
        assert sf.schoener_overlap(y, x) == got
        assert sf.schoener_overlap(3.0 * x, y) == pytest.approx(got, abs=1e-14)
        assert 0.0 <= got <= 1.0


def test_special_cases() -> None:
    assert sf.schoener_overlap([1.0, 2.0, 3.0, 0.0], [2.0, 4.0, 6.0, 0.0]) == (
        pytest.approx(1.0, abs=1e-15)
    )
    assert sf.schoener_overlap([1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]) == 0.0
    assert sf.schoener_overlap([1e308, 1e308], [1.0, 3.0]) == 0.75


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
        sf.schoener_overlap(x, y)
