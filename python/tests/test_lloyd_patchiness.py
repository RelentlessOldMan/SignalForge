"""Lloyd's index of patchiness (ADR 0610)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(610)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 1.0
        got = sf.lloyd_patchiness(x)
        assert got == pytest.approx(sf.lloyd_mean_crowding(x) / float(np.mean(x)), rel=1e-13)
        assert sf.lloyd_patchiness(x[::-1]) == pytest.approx(got, rel=1e-14, abs=1e-14)
        assert got >= 0.0


def test_poisson_counts_are_near_one() -> None:
    x = np.random.default_rng(1).poisson(4.0, 20000).astype(float)
    assert sf.lloyd_patchiness(x) == pytest.approx(1.0, abs=0.02)


def test_special_cases() -> None:
    assert sf.lloyd_patchiness([1.0, 1.0, 0.0]) == 0.0
    assert sf.lloyd_patchiness([0.0, 0.0, 6.0]) == pytest.approx(2.5, abs=1e-15)
    assert sf.lloyd_patchiness([1e308, 1e308]) == 1.0


@pytest.mark.parametrize(
    "counts",
    [[], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.0, np.inf], [1.5, 2.0], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.lloyd_patchiness(counts)
