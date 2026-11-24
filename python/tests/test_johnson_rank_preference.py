"""Johnson's rank preference index (ADR 0608)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _descending_ranks(v: np.ndarray) -> np.ndarray:
    n = v.size
    out = np.empty(n)
    for i in range(n):
        out[i] = np.sum(v > v[i]) + (np.sum(v == v[i]) + 1) / 2
    return out


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(608)
    for _ in range(20):
        x = rng.integers(0, 4, 12).astype(float)
        available = rng.integers(1, 5, 12).astype(float)
        x[0] = 1.0
        got = sf.johnson_rank_preference(x, available)
        np.testing.assert_array_equal(got, _descending_ranks(x) - _descending_ranks(available))
        assert float(got.sum()) == 0.0
        np.testing.assert_array_equal(sf.johnson_rank_preference(3.0 * x, available + 1.0), got)
        np.testing.assert_array_equal(
            sf.johnson_rank_preference(available, available), np.zeros(12)
        )


def test_special_cases() -> None:
    np.testing.assert_array_equal(
        sf.johnson_rank_preference([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]), [2.0, 0.0, -2.0]
    )
    np.testing.assert_array_equal(
        sf.johnson_rank_preference([1.0, 1.0, 0.0], [1.0, 2.0, 3.0]), [-1.5, -0.5, 2.0]
    )
    np.testing.assert_array_equal(sf.johnson_rank_preference([2.0], [5.0]), [0.0])


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
    ],
)
def test_rejects_bad_arguments(x: list[float], available: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.johnson_rank_preference(x, available)
