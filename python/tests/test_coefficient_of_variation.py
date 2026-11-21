"""The coefficient of variation (ADR 0513)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_population_standard_deviation_over_the_mean() -> None:
    rng = np.random.default_rng(276)
    for n in range(1, 30):
        x = rng.random(n) * 10
        want = float(np.std(x) / np.mean(x))
        v = sf.coefficient_of_variation(x)
        assert v == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert sf.coefficient_of_variation(3.5 * x) == pytest.approx(v, rel=1e-12, abs=1e-14)
        assert 0 <= v <= math.sqrt(n - 1) + 1e-12


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [-2.0, 1.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.coefficient_of_variation(bad)
