"""Gleason's index (ADR 0543)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_count_and_total() -> None:
    rng = np.random.default_rng(306)
    for n in range(1, 30):
        x = rng.integers(0, 5, n).astype(float)
        x[0] += 2.0
        d = sf.gleason_index(x)
        log_total = math.log(float(np.sum(x)))
        assert d == pytest.approx(np.count_nonzero(x) / log_total, rel=1e-14)
        assert d > 0
    assert sf.gleason_index([0.0, 7.0, 0.0]) == pytest.approx(1 / math.log(7.0), rel=1e-15)


@pytest.mark.parametrize(
    "bad", [[], [1.0], [0.5, 0.5], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.gleason_index(bad)
