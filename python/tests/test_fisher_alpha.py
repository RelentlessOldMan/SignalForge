"""Fisher's alpha (ADR 0550)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_solves_the_log_series() -> None:
    rng = np.random.default_rng(313)
    for n in range(1, 30):
        x = rng.integers(0, 40, n).astype(float)
        x[0] += 2.0
        total = float(np.sum(x))
        k = np.count_nonzero(x)
        a = sf.fisher_alpha(x)
        assert a * np.log1p(total / a) == pytest.approx(k, rel=1e-12)
        assert sf.fisher_alpha(rng.permutation(x)) == a
    assert sf.fisher_alpha([3.0, 1.0]) == sf.fisher_alpha([2.0, 0.0, 2.0])


def test_rises_with_the_kinds() -> None:
    low = sf.fisher_alpha([7.0, 1.0])
    high = sf.fisher_alpha([3.0, 3.0, 2.0])
    assert low < high


@pytest.mark.parametrize(
    "bad", [[], [1.0], [1.0, 1.0], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [1.0, np.inf]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.fisher_alpha(bad)
