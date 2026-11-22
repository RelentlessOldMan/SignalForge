"""Strong's dominance (ADR 0549)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_lorenz_gap() -> None:
    rng = np.random.default_rng(312)
    for n in range(1, 30):
        x = rng.random(n) * 10
        x[0] += 0.5
        pos = np.sort(x[x > 0])[::-1]
        k = pos.size
        gaps = np.cumsum(pos) / np.sum(x) - np.arange(1, k + 1) / k
        d = sf.strong_dominance(x)
        assert d == pytest.approx(max(0.0, float(np.max(gaps))), rel=1e-12, abs=1e-15)
        assert 0 <= d < 1
        assert sf.strong_dominance(rng.permutation(x)) == pytest.approx(d, rel=1e-12, abs=1e-15)
    assert sf.strong_dominance([3.0, 3.0, 0.0, 3.0]) == 0.0


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.strong_dominance(bad)
