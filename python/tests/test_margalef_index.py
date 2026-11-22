"""Margalef's index (ADR 0542)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_count_and_total() -> None:
    rng = np.random.default_rng(305)
    for n in range(1, 30):
        x = rng.integers(0, 5, n).astype(float)
        x[0] += 2.0
        d = sf.margalef_index(x)
        want = (np.count_nonzero(x) - 1) / math.log(float(np.sum(x)))
        assert d == pytest.approx(want, rel=1e-14, abs=1e-15)
        assert d >= 0
    assert sf.margalef_index([0.0, 7.0, 0.0]) == 0.0


@pytest.mark.parametrize(
    "bad", [[], [1.0], [0.5, 0.5], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.margalef_index(bad)
