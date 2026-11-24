"""Hurlbert's niche breadth (ADR 0601)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(601)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        available = rng.uniform(0.5, 4.0, 12)
        x[0] = 1.0
        p = x / x.sum()
        r = available / available.sum()
        want = 1.0 / float(np.sum(p * p / r))
        got = sf.hurlbert_niche_breadth(x, available)
        assert got == pytest.approx(want, rel=1e-14)
        least = float(r.min())
        assert sf.hurlbert_niche_breadth(x, available, standardized=True) == pytest.approx(
            (want - least) / (1.0 - least), rel=1e-13, abs=1e-15
        )
        assert sf.hurlbert_niche_breadth(3.0 * x, 0.5 * available) == pytest.approx(got, rel=1e-14)
        assert least * (1.0 - 1e-14) <= got <= 1.0
        assert sf.hurlbert_niche_breadth(available, available) == pytest.approx(1.0, abs=1e-14)


def test_special_cases() -> None:
    assert sf.hurlbert_niche_breadth([1.0, 1.0], [1.0, 3.0]) == 0.75
    assert sf.hurlbert_niche_breadth([1.0, 0.0], [1.0, 3.0], standardized=True) == 0.0
    assert sf.hurlbert_niche_breadth([2.0], [5.0]) == 1.0
    assert sf.hurlbert_niche_breadth([1e308, 1e308], [1e308, 1e308]) == 1.0


@pytest.mark.parametrize(
    ("x", "available"),
    [
        ([], []),
        ([1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 1.0]),
        ([1.0, -1.0], [1.0, 1.0]),
        ([1.0, np.nan], [1.0, 1.0]),
        ([[1.0, 2.0]], [[1.0, 1.0]]),
        ([1.0, 2.0], [1.0, 0.0]),
        ([1.0, 2.0, 3.0], [1e300, 5e-324, 1.0]),
        ([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]),
    ],
)
def test_rejects_bad_arguments(x: list[float], available: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hurlbert_niche_breadth(x, available)


def test_rejects_one_kind_standardized() -> None:
    with pytest.raises(ValueError):
        sf.hurlbert_niche_breadth([2.0], [5.0], standardized=True)
