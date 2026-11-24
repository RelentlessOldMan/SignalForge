"""Savage's selection ratio (ADR 0606)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(606)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        available = rng.uniform(0.5, 4.0, 12)
        x[0] = 1.0
        p = x / x.sum()
        r = available / available.sum()
        got = sf.savage_selection_ratio(x, available)
        np.testing.assert_allclose(got, p / r, rtol=1e-14, atol=1e-15)
        np.testing.assert_allclose(got / got.sum(), sf.manly_alpha(x, available), rtol=1e-14)
        assert float(np.sum(got * r)) == pytest.approx(1.0, abs=1e-14)
        np.testing.assert_allclose(
            sf.savage_selection_ratio(3.0 * x, 0.5 * available), got, rtol=1e-14
        )
        np.testing.assert_array_equal(sf.savage_selection_ratio(available, available), np.ones(12))


def test_special_cases() -> None:
    np.testing.assert_array_equal(sf.savage_selection_ratio([1.0, 0.0], [1.0, 3.0]), [4.0, 0.0])
    np.testing.assert_allclose(sf.savage_selection_ratio([1.0, 1.0], [1.0, 3.0]), [2.0, 2 / 3])
    np.testing.assert_array_equal(sf.savage_selection_ratio([2.0], [5.0]), [1.0])


@pytest.mark.parametrize(
    ("x", "available"),
    [
        ([], []),
        ([1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 1.0]),
        ([1.0, -1.0], [1.0, 1.0]),
        ([1.0, np.nan], [1.0, 1.0]),
        ([[1.0, 2.0]], [[1.0, 1.0]]),
        ([1.0, 2.0], [1.0, 0.0]),
        ([1.0, 2.0, 3.0], [1e300, 5e-324, 1.0]),
        ([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]),
    ],
)
def test_rejects_bad_arguments(x: list[float], available: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.savage_selection_ratio(x, available)
