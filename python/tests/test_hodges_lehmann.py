"""The Hodges-Lehmann shift estimate (ADR 0406)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_median_of_the_differences() -> None:
    rng = np.random.default_rng(149)
    x, y = rng.normal(0.4, 1.0, 50), rng.normal(0.0, 2.0, 35)
    expected = np.median(np.subtract.outer(x, y))
    assert sf.hodges_lehmann(x, y) == pytest.approx(expected, rel=1e-14)


def test_is_antisymmetric_and_follows_a_shift() -> None:
    rng = np.random.default_rng(150)
    x, y = rng.normal(0.3, 1.0, 30), rng.normal(0.0, 1.0, 21)
    assert sf.hodges_lehmann(y, x) == -sf.hodges_lehmann(x, y)
    assert sf.hodges_lehmann(x + 2.0, y) == pytest.approx(sf.hodges_lehmann(x, y) + 2.0)


def test_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        sf.hodges_lehmann([], [1.0])
