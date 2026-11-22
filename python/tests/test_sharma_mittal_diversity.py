"""The Sharma-Mittal diversity of counts (ADR 0570)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(570)
    x = rng.uniform(0.1, 4.0, 12)
    p = x / np.sum(x)
    for q in [0.3, 0.8, 1.5, 2.0, 3.5]:
        for r in [-2.0, 0.0, 0.5, 2.5]:
            want = (float(np.sum(p**q)) ** ((1.0 - r) / (1.0 - q)) - 1.0) / (1.0 - r)
            assert sf.sharma_mittal_diversity(x, q, r) == pytest.approx(want, rel=1e-12)


def test_special_cases() -> None:
    x = [2.0, 0.5, 3.25, 1.0, 0.0]
    for q in [0.0, 0.5, 1.0, 2.0, 6.0]:
        renyi = sf.renyi_diversity(x, q)
        assert sf.sharma_mittal_diversity(x, q, 1.0) == renyi
        assert sf.sharma_mittal_diversity(x, q, 1.0 + 1e-9) == pytest.approx(renyi, rel=1e-8)
        hill = sf.hill_number(x, q) - 1.0
        assert sf.sharma_mittal_diversity(x, q, 0.0) == pytest.approx(hill, rel=1e-13)
    for q in [0.0, 0.5, 2.0, 6.0]:
        tsallis = sf.tsallis_diversity(x, q)
        assert sf.sharma_mittal_diversity(x, q, q) == pytest.approx(tsallis, rel=1e-13)
    assert math.isclose(sf.sharma_mittal_diversity([0.0, 5.0], 2.0, -4.0), 0.0, abs_tol=0.0)


@pytest.mark.parametrize(
    ("bad", "q", "r"),
    [
        ([], 1.0, 0.0),
        ([0.0], 1.0, 0.0),
        ([1.0, -1.0], 1.0, 0.0),
        ([1.0], -0.5, 0.0),
        ([1.0], 1.0, np.inf),
        ([1.0], 1.0, np.nan),
    ],
)
def test_rejects_bad_arguments(bad: list[float], q: float, r: float) -> None:
    with pytest.raises(ValueError):
        sf.sharma_mittal_diversity(bad, q, r)
