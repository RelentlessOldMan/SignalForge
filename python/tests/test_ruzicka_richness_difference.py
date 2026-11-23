"""The richness-difference part of the Ruzicka dissimilarity (ADR 0587)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_adds_to_the_ruzicka_dissimilarity() -> None:
    rng = np.random.default_rng(587)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        a = float(np.minimum(x, y).sum())
        b = float(x.sum()) - a
        c = float(y.sum()) - a
        got = sf.ruzicka_richness_difference(x, y)
        assert got == pytest.approx(abs(b - c) / (a + b + c), rel=1e-12, abs=1e-14)
        assert sf.ruzicka_richness_difference(y, x) == got
        total = got + sf.ruzicka_replacement(x, y)
        assert total == pytest.approx(1.0 - sf.ruzicka_similarity(x, y), rel=1e-12, abs=1e-14)


def test_special_cases() -> None:
    x = [1.0, 1.0, 0.0, 1.0]
    y = [1.0, 0.0, 0.0, 0.0]
    assert sf.ruzicka_richness_difference(x, y) == pytest.approx(
        sf.podani_richness_difference(x, y)
    )
    assert sf.ruzicka_richness_difference([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert sf.ruzicka_richness_difference([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == 0.5


@pytest.mark.parametrize(
    ("x", "y"),
    [
        ([], []),
        ([1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 2.0]),
        ([1.0, -1.0], [1.0, 2.0]),
        ([1.0, np.nan], [1.0, 2.0]),
        ([[1.0, 2.0]], [[1.0, 2.0]]),
    ],
)
def test_rejects_bad_arguments(x: list[float], y: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.ruzicka_richness_difference(x, y)
