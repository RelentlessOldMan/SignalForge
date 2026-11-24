"""Cassie's index (ADR 0614)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(614)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 1.0
        got = sf.cassie_index(x)
        m = float(np.mean(x))
        assert got == pytest.approx((float(np.var(x, ddof=1)) - m) / m**2, rel=1e-13, abs=1e-14)
        assert got == pytest.approx(sf.david_moore_clumping(x) / m, rel=1e-13, abs=1e-14)
        assert sf.cassie_index(x[::-1]) == pytest.approx(got, rel=1e-13, abs=1e-14)


def test_negative_binomial_counts_estimate_one_over_k() -> None:
    x = np.random.default_rng(1).negative_binomial(2.0, 0.4, 40000).astype(float)
    assert sf.cassie_index(x) == pytest.approx(0.5, abs=0.02)


def test_special_cases() -> None:
    assert sf.cassie_index([2.0, 2.0, 2.0]) == pytest.approx(-0.5, abs=1e-15)
    assert sf.cassie_index([0.0, 0.0, 6.0]) == pytest.approx(2.5, abs=1e-14)
    assert sf.cassie_index([1e308, 0.0]) == 2.0


@pytest.mark.parametrize(
    "counts",
    [[], [5.0], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.5, 2.0], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.cassie_index(counts)
