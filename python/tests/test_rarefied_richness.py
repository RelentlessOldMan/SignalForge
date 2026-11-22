"""The rarefied richness (ADR 0552)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_binomials() -> None:
    rng = np.random.default_rng(315)
    for n in range(1, 25):
        x = rng.integers(0, 12, n).astype(float)
        x[0] += 1.0
        total = int(np.sum(x))
        k = np.count_nonzero(x)
        last = 0.0
        for size in range(1, total + 1):
            whole = math.comb(total, size)
            expected = sum(1 - math.comb(total - int(a), size) / whole for a in x if a > 0)
            e = sf.rarefied_richness(x, size)
            assert e == pytest.approx(expected, rel=1e-12, abs=1e-12)
            assert last - 1e-12 <= e <= k + 1e-12
            last = e
        assert sf.rarefied_richness(x, 1) == pytest.approx(1.0, rel=1e-14)
        assert sf.rarefied_richness(x, total) == k


@pytest.mark.parametrize("size", [0, -1, 7, 2.0, True])
def test_rejects_bad_sizes(size: int) -> None:
    with pytest.raises(ValueError):
        sf.rarefied_richness([1.0, 2.0, 3.0], size)


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.rarefied_richness(bad, 1)
