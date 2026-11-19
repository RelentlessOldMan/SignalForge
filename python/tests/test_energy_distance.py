"""The energy distance (ADR 0404)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_gap_formula() -> None:
    rng = np.random.default_rng(145)
    x, y = rng.normal(0.4, 1.0, 50), rng.normal(0.0, 2.0, 35)

    def gap(p: np.ndarray, q: np.ndarray) -> float:
        return float(np.mean(np.abs(p[:, None] - q[None, :])))

    expected = 2 * gap(x, y) - gap(x, x) - gap(y, y)
    assert sf.energy_distance(x, y) == pytest.approx(expected, rel=1e-12)


def test_is_symmetric_and_zero_for_the_same_values() -> None:
    rng = np.random.default_rng(146)
    x, y = rng.normal(0.3, 1.0, 30), rng.normal(0.0, 1.0, 20)
    assert sf.energy_distance(y, x) == pytest.approx(sf.energy_distance(x, y), rel=1e-12)
    assert sf.energy_distance(x, x[::-1]) == pytest.approx(0.0, abs=1e-13)


def test_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        sf.energy_distance([], [1.0])
