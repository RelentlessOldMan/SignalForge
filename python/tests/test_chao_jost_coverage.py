"""The Chao-Jost coverage (ADR 0553)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_counts() -> None:
    rng = np.random.default_rng(316)
    for n in range(1, 40):
        x = rng.integers(0, 5, n).astype(float)
        x[0] += 2.0
        total = float(np.sum(x))
        f1 = int(np.count_nonzero(x == 1))
        f2 = int(np.count_nonzero(x == 2))
        c = sf.chao_jost_coverage(x)
        if f1 == 0:
            assert c == 1.0
        else:
            a = (total - 1) * f1
            assert c == pytest.approx(1 - f1 / total * a / (a + 2 * f2), rel=1e-14)
        assert 0 <= c <= 1
        assert c >= sf.goods_coverage(x) - 1e-15


@pytest.mark.parametrize("bad", [[], [1.0], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.chao_jost_coverage(bad)
