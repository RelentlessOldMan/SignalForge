"""The Bonachela entropy (ADR 0560)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_double_sum() -> None:
    rng = np.random.default_rng(323)
    for n in range(1, 30):
        x = rng.integers(0, 12, n).astype(float)
        x[0] += 1.0
        total = int(np.sum(x))
        acc = 0.0
        for a in x:
            if a > 0:
                acc += (a + 1) * sum(1.0 / j for j in range(int(a) + 2, total + 3))
        h = sf.bonachela_entropy(x)
        assert h == pytest.approx(acc / (total + 2), rel=1e-13, abs=1e-15)
        assert h > 0
        assert sf.bonachela_entropy(rng.permutation(x)) == pytest.approx(h, rel=1e-13)


def test_one_kind() -> None:
    assert sf.bonachela_entropy([0.0, 8.0]) == pytest.approx(9 / 100, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [np.nan]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.bonachela_entropy(bad)
