"""Routledge's information beta of two presence records (ADR 0595)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(595)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = int(np.count_nonzero((x > 0) & (y > 0)))
        p = int(np.count_nonzero(x > 0))
        q = int(np.count_nonzero(y > 0))
        n = p + q
        # Shannon information of the pooled presences less the records' mean information.
        weights = np.array([2.0] * a + [1.0] * (n - 2 * a)) / n
        pooled = -float(np.sum(weights * np.log(weights)))
        mean = (p * math.log(p) + q * math.log(q)) / n
        got = sf.routledge_information_beta(x, y)
        assert got == pytest.approx(pooled - mean, abs=1e-14)
        assert sf.routledge_information_beta(y, x) == got
        assert 0.0 <= got <= math.log(2.0) + 1e-15


def test_special_cases() -> None:
    assert sf.routledge_information_beta([1.0, 2.0, 3.0, 0.0], [1e300, 4.0, 0.5, 0.0]) == 0.0
    assert sf.routledge_information_beta([1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]) == (
        pytest.approx(math.log(2.0), abs=1e-15)
    )


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
        sf.routledge_information_beta(x, y)
