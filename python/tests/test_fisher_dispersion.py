"""Fisher's index of dispersion statistic (ADR 0615)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(615)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 1.0
        got = sf.fisher_dispersion(x)
        m = float(np.mean(x))
        assert got == pytest.approx(float(np.sum((x - m) ** 2)) / m, rel=1e-13, abs=1e-13)
        assert got == pytest.approx(
            (x.size - 1) * (sf.david_moore_clumping(x) + 1.0), rel=1e-13, abs=1e-13
        )
        assert sf.fisher_dispersion(x[::-1]) == pytest.approx(got, rel=1e-13, abs=1e-13)


def test_poisson_counts_are_near_n_minus_one() -> None:
    x = np.random.default_rng(1).poisson(4.0, 20000).astype(float)
    assert sf.fisher_dispersion(x) == pytest.approx(19999.0, rel=0.05)


def test_special_cases() -> None:
    assert sf.fisher_dispersion([2.0, 2.0, 2.0]) == 0.0
    assert sf.fisher_dispersion([0.0, 0.0, 6.0]) == pytest.approx(12.0, abs=1e-13)
    assert sf.fisher_dispersion([1e308, 0.0]) == 1e308


@pytest.mark.parametrize(
    "counts",
    [
        [],
        [5.0],
        [0.0, 0.0],
        [1.0, -1.0],
        [1.0, np.nan],
        [1.5, 2.0],
        [[1.0, 2.0]],
        [1e308, 0.0, 0.0],
    ],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.fisher_dispersion(counts)
