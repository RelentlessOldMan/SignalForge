"""Green's index of dispersion (ADR 0611)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(611)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 2.0
        got = sf.green_index(x)
        m = float(np.mean(x))
        want = (float(np.var(x, ddof=1)) / m - 1.0) / (float(np.sum(x)) - 1.0)
        assert got == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert sf.green_index(x[::-1]) == pytest.approx(got, rel=1e-13, abs=1e-14)
        assert -1.0 <= got <= 1.0


def test_poisson_counts_are_near_zero() -> None:
    x = np.random.default_rng(1).poisson(4.0, 20000).astype(float)
    assert sf.green_index(x) == pytest.approx(0.0, abs=1e-4)


def test_special_cases() -> None:
    assert sf.green_index([0.0, 0.0, 6.0]) == pytest.approx(1.0, abs=1e-15)
    assert sf.green_index([2.0, 2.0, 2.0]) == pytest.approx(-0.2, abs=1e-15)
    assert sf.green_index([1e308, 0.0]) == 1.0


@pytest.mark.parametrize(
    "counts",
    [[], [5.0], [1.0, 0.0], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.5, 2.0], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.green_index(counts)
