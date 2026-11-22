"""Menhinick's index (ADR 0541)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_count_and_total() -> None:
    rng = np.random.default_rng(304)
    for n in range(1, 30):
        x = rng.integers(0, 5, n).astype(float)
        x[0] += 1.0
        d = sf.menhinick_index(x)
        want = np.count_nonzero(x) / math.sqrt(float(np.sum(x)))
        assert d == pytest.approx(want, rel=1e-14)
        assert sf.menhinick_index(4.0 * x) == pytest.approx(d / 2, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.menhinick_index(bad)
