"""Eberhardt's index (ADR 0620)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(620)
    for _ in range(20):
        u = rng.uniform(0.0, 2.0, 30)
        got = sf.eberhardt_index(u)
        assert got == pytest.approx(u.size * float(np.sum(u**2)) / float(np.sum(u)) ** 2, rel=1e-14)
        assert sf.eberhardt_index(7.0 * u) == pytest.approx(got, rel=1e-14)
        assert 1.0 <= got <= u.size


def test_rayleigh_distances_give_four_over_pi() -> None:
    rng = np.random.default_rng(1)
    u = rng.rayleigh(1.0, 200_000)
    assert sf.eberhardt_index(u) == pytest.approx(4.0 / math.pi, abs=0.01)


def test_special_cases() -> None:
    assert sf.eberhardt_index([2.5]) == 1.0
    assert sf.eberhardt_index([0.0, 0.0, 4.0]) == 3.0
    assert sf.eberhardt_index([1e300, 3e300]) == pytest.approx(1.25, rel=1e-15)


@pytest.mark.parametrize(
    "u",
    [[], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.0, np.inf], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(u: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.eberhardt_index(u)
