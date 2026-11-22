"""Zhang's entropy (ADR 0561)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(324)
    for n in range(1, 25):
        x = rng.integers(0, 8, n).astype(float)
        x[0] += 2.0
        total = int(np.sum(x))
        acc = 0.0
        for a in x[x > 0]:
            factors = 1.0 - (a - 1.0) / (total - 1.0 - np.arange(total - 1))
            prods = np.cumprod(factors)
            acc += a / total * float(np.sum(prods / np.arange(1, total)))
        h = sf.zhang_entropy(x)
        assert h == pytest.approx(acc, rel=1e-11, abs=1e-13)
        assert sf.zhang_entropy(rng.permutation(x)) == pytest.approx(h, rel=1e-13, abs=1e-15)
    assert sf.zhang_entropy([0.0, 7.0]) == 0.0


def test_is_near_the_plug_in_for_a_large_sample() -> None:
    x = np.array([1000.0, 2000.0, 3000.0, 4000.0])
    p = x / np.sum(x)
    assert sf.zhang_entropy(x) == pytest.approx(float(-np.sum(p * np.log(p))), abs=1e-3)


@pytest.mark.parametrize(
    "bad", [[], [1.0], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e4, 1.0], [np.nan]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.zhang_entropy(bad)
