"""The turnover part of the Jaccard dissimilarity (ADR 0578)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(578)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = int(np.count_nonzero((x > 0) & (y > 0)))
        b = int(np.count_nonzero((x > 0) & (y == 0)))
        c = int(np.count_nonzero((x == 0) & (y > 0)))
        want = 2 * min(b, c) / (a + 2 * min(b, c))
        assert sf.jaccard_turnover(x, y) == want
        assert sf.jaccard_turnover(y, x) == want
        assert sf.jaccard_turnover(x, y) >= sf.simpson_beta(x, y) - 1e-15


def test_special_cases() -> None:
    assert sf.jaccard_turnover([1.0, 2.0, 3.0, 0.0], [1e300, 0.0, 7.0, 0.0]) == 0.0
    assert sf.jaccard_turnover([1.0, 0.0], [0.0, 1.0]) == 1.0


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
        sf.jaccard_turnover(x, y)
