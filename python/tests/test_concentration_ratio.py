"""The concentration ratio (ADR 0524)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

import signalforge as sf


def test_sums_the_largest_shares() -> None:
    rng = np.random.default_rng(287)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        desc = np.sort(x)[::-1]
        prev = 0.0
        for k in range(1, n + 1):
            c = sf.concentration_ratio(x, k)
            assert c == pytest.approx(float(np.sum(desc[:k]) / np.sum(x)), rel=1e-12)
            assert c >= prev
            assert c >= k / n - 1e-14
            prev = c
        assert sf.concentration_ratio(x, n) == pytest.approx(1.0, rel=1e-14)
        assert sf.concentration_ratio(x, 1) >= sf.herfindahl_index(x) - 1e-14


@pytest.mark.parametrize(
    ("bad", "k"),
    [
        ([], 1),
        ([1.0, -1.0], 1),
        ([0.0, 0.0], 1),
        ([1.0, np.inf], 1),
        ([[1.0, 2.0]], 1),
        ([1.0, 2.0], 0),
        ([1.0, 2.0], 3),
        ([1.0, 2.0], 1.0),
        ([1.0, 2.0], True),
    ],
)
def test_rejects_bad_arguments(bad: list[float], k: Any) -> None:
    with pytest.raises(ValueError):
        sf.concentration_ratio(bad, k)
