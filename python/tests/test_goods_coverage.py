"""Good's coverage (ADR 0544)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_singletons() -> None:
    rng = np.random.default_rng(307)
    for n in range(1, 30):
        x = rng.integers(0, 4, n).astype(float)
        x[0] += 1.0
        c = sf.goods_coverage(x)
        assert c == pytest.approx(1 - np.count_nonzero(x == 1) / float(np.sum(x)), rel=1e-15)
        assert 0 <= c <= 1
    assert sf.goods_coverage([1.0, 1.0, 1.0]) == 0.0
    assert sf.goods_coverage([2.0, 3.0]) == 1.0


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.goods_coverage(bad)
