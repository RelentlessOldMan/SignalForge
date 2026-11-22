"""The Chao-Shen entropy (ADR 0554)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_estimate() -> None:
    rng = np.random.default_rng(317)
    for n in range(1, 40):
        x = rng.integers(0, 7, n).astype(float)
        x[0] += 1.0
        total = float(np.sum(x))
        f1 = int(np.count_nonzero(x == 1))
        if f1 == total:
            f1 -= 1
        a = (1 - f1 / total) * x[x > 0] / total
        expected = float(-np.sum(a * np.log(a) / (1 - (1 - a) ** total)))
        h = sf.chao_shen_entropy(x)
        assert h == pytest.approx(expected, rel=1e-12, abs=1e-14)
        assert h >= 0
        assert sf.chao_shen_entropy(rng.permutation(x)) == pytest.approx(h, rel=1e-13, abs=1e-15)


def test_no_singletons_in_a_large_sample_is_near_the_plug_in() -> None:
    x = np.array([1000.0, 2000.0, 3000.0, 4000.0])
    p = x / np.sum(x)
    assert sf.chao_shen_entropy(x) == pytest.approx(float(-np.sum(p * np.log(p))), rel=1e-14)


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [np.nan]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.chao_shen_entropy(bad)
