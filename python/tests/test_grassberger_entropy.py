"""The Grassberger entropy (ADR 0559)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

EULER = 0.5772156649015329


def _g(n: int) -> float:
    """Grassberger's G(n) from the digamma definition at whole and half-whole points."""

    def whole(k: int) -> float:
        return -EULER + sum(1.0 / i for i in range(1, k))

    def half(m: int) -> float:
        return -EULER - 2 * math.log(2.0) + sum(1.0 / (i + 0.5) for i in range(m))

    diff = half(n // 2) - whole(n // 2) if n % 2 == 0 else whole((n + 1) // 2) - half(n // 2)
    return whole(n) + (diff if n % 2 == 0 else -diff) / 2


def test_matches_the_digamma_definition() -> None:
    rng = np.random.default_rng(322)
    for n in range(1, 30):
        x = rng.integers(0, 12, n).astype(float)
        x[0] += 1.0
        total = float(np.sum(x))
        expected = math.log(total) - sum(a * _g(int(a)) for a in x if a > 0) / total
        h = sf.grassberger_entropy(x)
        assert h == pytest.approx(expected, rel=1e-12, abs=1e-13)
        assert sf.grassberger_entropy(rng.permutation(x)) == pytest.approx(h, rel=1e-13, abs=1e-14)


def test_approaches_the_plug_in_for_large_counts() -> None:
    x = np.array([100000.0, 200000.0, 300000.0])
    p = x / np.sum(x)
    assert sf.grassberger_entropy(x) == pytest.approx(float(-np.sum(p * np.log(p))), abs=1e-5)


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [np.nan]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.grassberger_entropy(bad)
