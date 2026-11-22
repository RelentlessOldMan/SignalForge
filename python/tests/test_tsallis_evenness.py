"""Tsallis evenness (ADR 0569)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_tsallis_diversity_over_its_maximum() -> None:
    rng = np.random.default_rng(569)
    x = rng.uniform(0.1, 4.0, 12)
    x[3] = 0.0
    for q in [0.0, 0.5, 1.0, 1.0001, 2.0, 7.0]:
        top = math.log(11) if q == 1 else (1.0 - 11.0 ** (1.0 - q)) / (q - 1.0)
        want = sf.tsallis_diversity(x, q) / top
        assert sf.tsallis_evenness(x, q) == pytest.approx(want, rel=1e-10)
    assert sf.tsallis_evenness(x, 0.0) == pytest.approx(1.0, rel=1e-14)


def test_bounds() -> None:
    assert sf.tsallis_evenness([3.0, 3.0, 3.0], 2.0) == pytest.approx(1.0, rel=1e-14)
    e = sf.tsallis_evenness([1e9, 1.0, 1.0, 1.0], 2.0)
    assert 0.0 < e < 1e-7


@pytest.mark.parametrize(
    ("bad", "q"), [([], 1.0), ([0.0, 4.0], 1.0), ([1.0, -1.0], 1.0), ([1.0, 2.0], -1.0)]
)
def test_rejects_bad_arguments(bad: list[float], q: float) -> None:
    with pytest.raises(ValueError):
        sf.tsallis_evenness(bad, q)
