"""The Clark-Evans test statistic (ADR 0617)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(617)
    for _ in range(20):
        d = rng.uniform(0.0, 2.0, 30)
        rho = float(rng.uniform(0.1, 5.0))
        got = sf.clark_evans_z(d, rho)
        r_e = 0.5 / math.sqrt(rho)
        sigma = math.sqrt((4.0 - math.pi) / (4.0 * math.pi * rho * d.size))
        assert got == pytest.approx((float(np.mean(d)) - r_e) / sigma, rel=1e-12, abs=1e-12)
        assert got == pytest.approx(
            (float(np.mean(d)) - r_e) / (0.26136 / math.sqrt(d.size * rho)), rel=1e-4
        )


def test_random_patterns_are_near_standard_normal() -> None:
    rng = np.random.default_rng(1)
    n = 400
    zs = []
    for _ in range(100):
        pts = rng.uniform(0.0, 1.0, (n, 2))
        diff = np.abs(pts[:, None, :] - pts[None, :, :])
        diff = np.minimum(diff, 1.0 - diff)
        dist = np.sqrt((diff**2).sum(axis=2))
        np.fill_diagonal(dist, np.inf)
        zs.append(sf.clark_evans_z(dist.min(axis=1), float(n)))
    assert float(np.mean(zs)) == pytest.approx(0.0, abs=0.35)


def test_special_cases() -> None:
    assert sf.clark_evans_z([0.5, 0.5], 1.0) == 0.0
    assert sf.clark_evans_z([0.25], 16.0) == pytest.approx(
        math.sqrt(math.pi / (4.0 - math.pi)), rel=1e-15
    )


@pytest.mark.parametrize(
    ("distances", "density"),
    [
        ([], 1.0),
        ([1.0, -1.0], 1.0),
        ([1.0, np.nan], 1.0),
        ([[1.0, 2.0]], 1.0),
        ([1.0], 0.0),
        ([1.0], np.inf),
        ([1e308, 1e308], 0.25),
    ],
)
def test_rejects_bad_arguments(distances: list[float], density: float) -> None:
    with pytest.raises(ValueError):
        sf.clark_evans_z(distances, density)


class _Counted:
    """An array-like that counts its conversions."""

    def __init__(self, values: list[float]) -> None:
        self.values = values
        self.calls = 0

    def __array__(self, dtype: object = None, copy: object = None) -> np.ndarray:
        self.calls += 1
        return np.array(self.values, dtype=np.float64)


def test_clark_evans_z_converts_once() -> None:
    x = _Counted([1.0, 2.0, 0.5])
    sf.clark_evans_z(x, 1.0)
    assert x.calls == 1
