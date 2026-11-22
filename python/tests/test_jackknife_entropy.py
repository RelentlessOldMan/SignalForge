"""The jackknife Shannon entropy (ADR 0558)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _plug(x: np.ndarray) -> float:
    p = x[x > 0] / np.sum(x)
    return float(-np.sum(p * np.log(p)))


def test_matches_the_jackknife_over_individuals() -> None:
    rng = np.random.default_rng(321)
    for n in range(1, 30):
        x = rng.integers(0, 10, n).astype(float)
        x[0] += 2.0
        total = float(np.sum(x))
        acc = 0.0
        for i in range(n):
            if x[i] > 0:
                y = x.copy()
                y[i] -= 1.0
                acc += x[i] * _plug(y)
        expected = total * _plug(x) - (total - 1) / total * acc
        h = sf.jackknife_entropy(x)
        assert h == pytest.approx(expected, rel=1e-10, abs=1e-11)
        assert sf.jackknife_entropy(rng.permutation(x)) == pytest.approx(h, rel=1e-10, abs=1e-11)
    assert sf.jackknife_entropy([0.0, 7.0]) == pytest.approx(0.0, abs=1e-13)


def test_is_above_the_plug_in_for_even_shares() -> None:
    x = np.array([3.0, 3.0, 3.0, 3.0])
    assert sf.jackknife_entropy(x) > _plug(x)


@pytest.mark.parametrize(
    "bad", [[], [1.0], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [np.nan]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.jackknife_entropy(bad)
