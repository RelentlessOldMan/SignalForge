"""The Chao1 richness (ADR 0545)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_counts() -> None:
    rng = np.random.default_rng(308)
    for n in range(1, 30):
        x = rng.integers(0, 4, n).astype(float)
        x[0] += 1.0
        k = np.count_nonzero(x)
        f1 = int(np.count_nonzero(x == 1))
        f2 = int(np.count_nonzero(x == 2))
        s = sf.chao1_richness(x)
        assert s == pytest.approx(k + f1 * (f1 - 1) / (2 * (f2 + 1)), rel=1e-15)
        assert s >= k
    assert sf.chao1_richness([4.0, 0.0, 3.0]) == 2.0


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.chao1_richness(bad)
