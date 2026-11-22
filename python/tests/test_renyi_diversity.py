"""The Renyi diversity of counts (ADR 0566)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_log_of_the_renyi_diversity() -> None:
    rng = np.random.default_rng(566)
    x = rng.uniform(0.1, 4.0, 12)
    x[5] = 0.0
    for q in [0.0, 0.2, 0.99, 1.0, 1.01, 1.7, 2.0, 30.0]:
        want = math.log(sf.hill_number(x, q))
        assert sf.renyi_diversity(x, q) == pytest.approx(want, rel=1e-13, abs=1e-14)
    assert sf.renyi_diversity(x, 0.0) == math.log(11)


def test_is_continuous_at_order_one() -> None:
    x = [2.0, 0.5, 3.25, 1.0]
    h = sf.renyi_diversity(x, 1.0)
    for q in [1.0 - 1e-9, 1.0 + 1e-9]:
        assert sf.renyi_diversity(x, q) == pytest.approx(h, rel=1e-8)
    assert sf.renyi_diversity([0.0, 5.0], 3.0) == 0.0


@pytest.mark.parametrize(("bad", "q"), [([], 1.0), ([0.0], 1.0), ([1.0, -1.0], 1.0), ([1.0], -1.0)])
def test_rejects_bad_arguments(bad: list[float], q: float) -> None:
    with pytest.raises(ValueError):
        sf.renyi_diversity(bad, q)
