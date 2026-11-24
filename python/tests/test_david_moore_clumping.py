"""David and Moore's index of clumping (ADR 0613)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(613)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 1.0
        got = sf.david_moore_clumping(x)
        want = float(np.var(x, ddof=1)) / float(np.mean(x)) - 1.0
        assert got == pytest.approx(want, rel=1e-13, abs=1e-14)
        assert sf.david_moore_clumping(x[::-1]) == pytest.approx(got, rel=1e-13, abs=1e-14)
        assert got >= -1.0


def test_poisson_counts_are_near_zero() -> None:
    x = np.random.default_rng(1).poisson(4.0, 20000).astype(float)
    assert sf.david_moore_clumping(x) == pytest.approx(0.0, abs=0.05)


def test_special_cases() -> None:
    assert sf.david_moore_clumping([2.0, 2.0, 2.0]) == -1.0
    assert sf.david_moore_clumping([0.0, 0.0, 6.0]) == pytest.approx(5.0, abs=1e-14)
    assert sf.david_moore_clumping([1e308, 0.0]) == 1e308


@pytest.mark.parametrize(
    "counts",
    [[], [5.0], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.5, 2.0], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.david_moore_clumping(counts)
