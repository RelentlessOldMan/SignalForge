"""Simpson's beta of two records (ADR 0576)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(576)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = int(np.count_nonzero((x > 0) & (y > 0)))
        b = int(np.count_nonzero((x > 0) & (y == 0)))
        c = int(np.count_nonzero((x == 0) & (y > 0)))
        want = min(b, c) / (a + min(b, c))
        assert sf.simpson_beta(x, y) == want
        assert sf.simpson_beta(y, x) == want
        assert sf.simpson_beta(x, y) <= sf.whittaker_beta(x, y) + 1e-15


def test_nested_records_have_no_turnover() -> None:
    assert sf.simpson_beta([1.0, 2.0, 3.0, 0.0], [1e300, 0.0, 7.0, 0.0]) == 0.0
    assert sf.simpson_beta([1.0, 0.0], [0.0, 1.0]) == 1.0


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
        sf.simpson_beta(x, y)
