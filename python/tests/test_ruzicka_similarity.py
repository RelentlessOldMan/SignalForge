"""The Ruzicka similarity of two records (ADR 0580)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(580)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        want = float(np.minimum(x, y).sum() / np.maximum(x, y).sum())
        got = sf.ruzicka_similarity(x, y)
        assert got == pytest.approx(want, rel=1e-14, abs=1e-15)
        assert sf.ruzicka_similarity(y, x) == got
        assert 0.0 <= got <= 1.0


def test_special_cases() -> None:
    assert sf.ruzicka_similarity([1.5e308, 1.5e308], [1.5e308, 0.0]) == 0.5
    assert sf.ruzicka_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert sf.ruzicka_similarity([1.0, 1.0, 0.0], [1.0, 0.0, 1.0]) == sf.jaccard_index(
        [1.0, 1.0, 0.0], [1.0, 0.0, 1.0]
    )


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
        sf.ruzicka_similarity(x, y)
