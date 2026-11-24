"""Morisita's index of dispersion (ADR 0612)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(612)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 2.0
        got = sf.morisita_dispersion(x)
        tot = float(np.sum(x))
        want = x.size * float(np.sum(x * (x - 1))) / (tot * (tot - 1))
        assert got == pytest.approx(want, rel=1e-13, abs=1e-14)
        assert sf.morisita_dispersion(x[::-1]) == pytest.approx(got, rel=1e-13, abs=1e-14)
        assert 0.0 <= got <= x.size


def test_poisson_counts_are_near_one() -> None:
    x = np.random.default_rng(1).poisson(4.0, 20000).astype(float)
    assert sf.morisita_dispersion(x) == pytest.approx(1.0, abs=0.02)


def test_special_cases() -> None:
    assert sf.morisita_dispersion([0.0, 0.0, 6.0]) == pytest.approx(3.0, abs=1e-14)
    assert sf.morisita_dispersion([1.0, 1.0, 0.0]) == 0.0
    assert sf.morisita_dispersion([1e308, 0.0]) == 2.0


@pytest.mark.parametrize(
    "counts",
    [[], [5.0], [1.0, 0.0], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.5, 2.0], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.morisita_dispersion(counts)
