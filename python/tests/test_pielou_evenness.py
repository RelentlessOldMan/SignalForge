"""Pielou's evenness (ADR 0528)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_entropy_and_hannah_kay() -> None:
    rng = np.random.default_rng(291)
    for n in range(2, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        j = sf.pielou_evenness(x)
        assert j == pytest.approx(float(-np.sum(sh * np.log(sh))) / math.log(n), rel=1e-12)
        hk = sf.hannah_kay_index(x, 1.0)
        assert j == pytest.approx(math.log(hk) / math.log(n), rel=1e-12)
        assert 0 <= j <= 1 + 1e-14
        assert sf.pielou_evenness(3.5 * x) == pytest.approx(j, rel=1e-12)
    assert sf.pielou_evenness([2.0] * 8) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [5.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.pielou_evenness(bad)
