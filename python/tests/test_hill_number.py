"""The Hill number (ADR 0563)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition_and_its_special_cases() -> None:
    rng = np.random.default_rng(563)
    x = rng.uniform(0.1, 4.0, 12)
    p = x / np.sum(x)
    for q in [0.2, 0.7, 0.99, 1.01, 1.3, 2.0, 4.0]:
        want = float(np.sum(p**q)) ** (1.0 / (1.0 - q))
        assert sf.hill_number(x, q) == pytest.approx(want, rel=1e-9)
    assert sf.hill_number(x, 0.0) == 12.0
    assert sf.hill_number(x, 1.0) == pytest.approx(math.exp(-float(np.sum(p * np.log(p)))))
    assert sf.hill_number(x, 2.0) == pytest.approx(1.0 / float(np.sum(p * p)))


def test_is_continuous_at_order_one() -> None:
    x = [2.0, 0.5, 3.25, 1.0]
    h = sf.hill_number(x, 1.0)
    for q in [1.0 - 1e-9, 1.0 + 1e-9]:
        assert sf.hill_number(x, q) == pytest.approx(h, rel=1e-8)


def test_large_orders_tend_to_the_largest_share() -> None:
    x = [1.0, 2.0, 5.0, 2.0]
    assert sf.hill_number(x, 1e5) == pytest.approx(2.0, rel=1e-4)
    assert math.isfinite(sf.hill_number(x, 1e300))


def test_falls_with_order() -> None:
    x = [1.0, 2.0, 5.0, 0.0, 2.0]
    values = [sf.hill_number(x, q) for q in [0.0, 0.5, 1.0, 1.5, 2.0, 8.0]]
    assert all(a >= b for a, b in itertools.pairwise(values))


@pytest.mark.parametrize(
    ("bad", "q"),
    [([], 1.0), ([0.0], 1.0), ([1.0, -1.0], 1.0), ([np.nan], 1.0), ([1.0], -1.0), ([1.0], np.inf)],
)
def test_rejects_bad_arguments(bad: list[float], q: float) -> None:
    with pytest.raises(ValueError):
        sf.hill_number(bad, q)
