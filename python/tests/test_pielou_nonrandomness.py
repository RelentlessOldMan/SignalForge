"""Pielou's index of non-randomness (ADR 0619)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(619)
    for _ in range(20):
        u = rng.uniform(0.0, 2.0, 30)
        rho = float(rng.uniform(0.1, 5.0))
        got = sf.pielou_nonrandomness(u, rho)
        assert got == pytest.approx(math.pi * rho * float(np.mean(u**2)), rel=1e-14)
        assert sf.pielou_nonrandomness(2.0 * u, rho / 4.0) == pytest.approx(got, rel=1e-14)


def test_random_pattern_is_near_one() -> None:
    rng = np.random.default_rng(1)
    n = 2000
    pts = rng.uniform(0.0, 1.0, (n, 2))
    q = rng.uniform(0.0, 1.0, (1000, 2))
    diff = np.abs(q[:, None, :] - pts[None, :, :])
    diff = np.minimum(diff, 1.0 - diff)
    u = np.sqrt((diff**2).sum(axis=2)).min(axis=1)
    assert sf.pielou_nonrandomness(u, float(n)) == pytest.approx(1.0, abs=0.12)


def test_special_cases() -> None:
    assert sf.pielou_nonrandomness([0.0, 0.0], 3.0) == 0.0
    assert sf.pielou_nonrandomness([1.0], 1.0) == pytest.approx(math.pi, rel=1e-15)
    assert sf.pielou_nonrandomness([1e200], 1e-300) == pytest.approx(math.pi * 1e100, rel=1e-14)


@pytest.mark.parametrize(
    ("u", "density"),
    [
        ([], 1.0),
        ([1.0, -1.0], 1.0),
        ([1.0, np.nan], 1.0),
        ([1.0, np.inf], 1.0),
        ([[1.0, 2.0]], 1.0),
        ([1.0], 0.0),
        ([1.0], -1.0),
        ([1.0], np.inf),
        ([1e150, 1e150], 1e10),
    ],
)
def test_rejects_bad_arguments(u: list[float], density: float) -> None:
    with pytest.raises(ValueError):
        sf.pielou_nonrandomness(u, density)
