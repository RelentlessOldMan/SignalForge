"""Hutcheson's variance (ADR 0556)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_variance_of_the_log_shares() -> None:
    rng = np.random.default_rng(319)
    for n in range(1, 40):
        x = rng.integers(0, 10, n).astype(float)
        x[0] += 1.0
        total = float(np.sum(x))
        p = x[x > 0] / total
        spread = float(np.sum(p * (np.log(p) - np.sum(p * np.log(p))) ** 2))
        expected = spread / total + (p.size - 1) / (2 * total * total)
        v = sf.hutcheson_variance(x)
        assert v == pytest.approx(expected, rel=1e-10, abs=1e-14)
        assert v >= -1e-15
        assert sf.hutcheson_variance(rng.permutation(x)) == pytest.approx(v, rel=1e-10, abs=1e-14)
    assert sf.hutcheson_variance([0.0, 7.0]) == 0.0


def test_shrinks_with_the_sample() -> None:
    small = sf.hutcheson_variance([1.0, 2.0, 3.0])
    large = sf.hutcheson_variance([100.0, 200.0, 300.0])
    assert large < small / 50


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [np.nan]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hutcheson_variance(bad)
