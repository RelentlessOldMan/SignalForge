"""Sheldon's evenness (ADR 0538)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_entropy_and_hannah_kay() -> None:
    rng = np.random.default_rng(301)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        e = sf.sheldon_evenness(x)
        assert e == pytest.approx(math.exp(float(-np.sum(sh * np.log(sh)))) / n, rel=1e-12)
        assert e == pytest.approx(sf.hannah_kay_index(x, 1.0) / n, rel=1e-12)
        assert 1 / n - 1e-14 <= e <= 1 + 1e-14
        assert sf.sheldon_evenness(3.5 * x) == pytest.approx(e, rel=1e-12)
    assert sf.sheldon_evenness([2.0] * 8) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.sheldon_evenness(bad)
