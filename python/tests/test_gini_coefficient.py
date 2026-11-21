"""The Gini coefficient (ADR 0510)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_absolute_difference_over_twice_the_mean() -> None:
    rng = np.random.default_rng(273)
    for n in range(1, 30):
        x = rng.random(n) * 10
        want = float(np.mean(np.abs(x[:, None] - x[None, :])) / (2 * np.mean(x)))
        v = sf.gini_coefficient(x)
        assert v == pytest.approx(want, rel=1e-12, abs=1e-15)
        assert sf.gini_coefficient(3.5 * x) == pytest.approx(v, rel=1e-13, abs=1e-15)
        assert 0 <= v <= 1 - 1 / n + 1e-15


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.gini_coefficient(bad)
