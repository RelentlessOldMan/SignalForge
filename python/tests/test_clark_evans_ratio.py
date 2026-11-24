"""The Clark-Evans aggregation index (ADR 0616)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(616)
    for _ in range(20):
        d = rng.uniform(0.0, 2.0, 30)
        rho = float(rng.uniform(0.1, 5.0))
        got = sf.clark_evans_ratio(d, rho)
        assert got == pytest.approx(float(np.mean(d)) / (0.5 / math.sqrt(rho)), rel=1e-14)
        assert sf.clark_evans_ratio(2.0 * d, rho / 4.0) == pytest.approx(got, rel=1e-14)


def test_random_pattern_is_near_one() -> None:
    rng = np.random.default_rng(1)
    n = 4000
    pts = rng.uniform(0.0, 1.0, (n, 2))
    diff = np.abs(pts[:, None, :] - pts[None, :, :])
    diff = np.minimum(diff, 1.0 - diff)
    dist = np.sqrt((diff**2).sum(axis=2))
    np.fill_diagonal(dist, np.inf)
    assert sf.clark_evans_ratio(dist.min(axis=1), float(n)) == pytest.approx(1.0, abs=0.03)


def test_special_cases() -> None:
    assert sf.clark_evans_ratio([0.0, 0.0], 3.0) == 0.0
    assert sf.clark_evans_ratio([0.25], 16.0) == 2.0
    assert sf.clark_evans_ratio([1e308, 1e308], 0.25) == 1e308


@pytest.mark.parametrize(
    ("distances", "density"),
    [
        ([], 1.0),
        ([1.0, -1.0], 1.0),
        ([1.0, np.nan], 1.0),
        ([1.0, np.inf], 1.0),
        ([[1.0, 2.0]], 1.0),
        ([1.0], 0.0),
        ([1.0], -1.0),
        ([1.0], np.inf),
        ([1.0], np.nan),
        ([1e308], 4.0),
    ],
)
def test_rejects_bad_arguments(distances: list[float], density: float) -> None:
    with pytest.raises(ValueError):
        sf.clark_evans_ratio(distances, density)
