"""The proportional similarity (ADR 0572)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition_on_shares() -> None:
    rng = np.random.default_rng(572)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 9)
        y = rng.uniform(0.0, 4.0, 9)
        p = x / np.sum(x)
        q = y / np.sum(y)
        want = float(np.sum(np.minimum(p, q)))
        assert sf.czekanowski_similarity(x, y) == pytest.approx(want, rel=1e-13)
        assert sf.czekanowski_similarity(y, x) == pytest.approx(want, rel=1e-15)
        half_l1 = 1.0 - 0.5 * float(np.sum(np.abs(p - q)))
        assert sf.czekanowski_similarity(x, y) == pytest.approx(half_l1, rel=1e-12)


def test_bounds_and_scale() -> None:
    same = sf.czekanowski_similarity([1.0, 2.0, 3.0], [3e-200, 6e-200, 9e-200])
    assert same == pytest.approx(1.0, rel=1e-15)
    assert sf.czekanowski_similarity([1.0, 0.0, 0.0], [0.0, 2.0, 5.0]) == 0.0
    assert sf.czekanowski_similarity([1e300, 1e300], [1.0, 1.0]) == pytest.approx(1.0, rel=1e-15)


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
        sf.czekanowski_similarity(x, y)
