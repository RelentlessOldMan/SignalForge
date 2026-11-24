"""Manly's alpha (ADR 0602)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(602)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        available = rng.uniform(0.5, 4.0, 12)
        x[0] = 1.0
        w = x / available
        got = sf.manly_alpha(x, available)
        np.testing.assert_allclose(got, w / w.sum(), rtol=1e-14, atol=1e-15)
        assert float(got.sum()) == pytest.approx(1.0, abs=1e-14)
        np.testing.assert_allclose(sf.manly_alpha(3.0 * x, 0.5 * available), got, rtol=1e-14)
        np.testing.assert_allclose(
            sf.manly_alpha(available, available), np.full(12, 1.0 / 12.0), rtol=1e-14
        )


def test_special_cases() -> None:
    np.testing.assert_array_equal(sf.manly_alpha([1.0, 1.0], [1.0, 3.0]), [0.75, 0.25])
    np.testing.assert_array_equal(sf.manly_alpha([1.0, 0.0], [1.0, 3.0]), [1.0, 0.0])
    np.testing.assert_array_equal(sf.manly_alpha([2.0], [5.0]), [1.0])
    np.testing.assert_array_equal(sf.manly_alpha([1e308, 1e308], [1e308, 1e308]), [0.5, 0.5])


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
        sf.manly_alpha(x, available)
