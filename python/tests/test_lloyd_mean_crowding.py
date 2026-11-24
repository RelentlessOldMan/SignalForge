"""Lloyd's mean crowding (ADR 0609)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(609)
    for _ in range(20):
        x = rng.integers(0, 9, 15).astype(float)
        x[0] = 1.0
        got = sf.lloyd_mean_crowding(x)
        assert got == pytest.approx(float(np.sum(x * (x - 1)) / np.sum(x)), rel=1e-14, abs=1e-14)
        assert sf.lloyd_mean_crowding(x[::-1]) == pytest.approx(got, rel=1e-14, abs=1e-14)
        assert sf.lloyd_mean_crowding(np.append(x, [0.0, 0.0])) == pytest.approx(
            got, rel=1e-14, abs=1e-14
        )
        assert got >= 0.0


def test_special_cases() -> None:
    assert sf.lloyd_mean_crowding([1.0, 1.0, 0.0]) == 0.0
    assert sf.lloyd_mean_crowding([5.0]) == pytest.approx(4.0, abs=1e-15)
    assert sf.lloyd_mean_crowding([1e308, 1e308]) == 1e308


@pytest.mark.parametrize(
    "counts",
    [[], [0.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.0, np.inf], [1.5, 2.0], [[1.0, 2.0]]],
)
def test_rejects_bad_arguments(counts: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.lloyd_mean_crowding(counts)
