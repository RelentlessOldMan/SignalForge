"""Glass's delta (ADR 0399)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_uses_the_control_spread_only() -> None:
    rng = np.random.default_rng(136)
    x, y = rng.normal(2.0, 5.0, 40), rng.normal(0.0, 1.0, 60)
    expected = (np.mean(x) - np.mean(y)) / np.std(y, ddof=1)
    assert sf.glass_delta(x, y) == pytest.approx(expected, rel=1e-12)


def test_does_not_depend_on_the_treated_spread() -> None:
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert sf.glass_delta([3.0, 3.0], y) == sf.glass_delta([0.0, 6.0], y)


def test_rejects_a_control_without_spread() -> None:
    with pytest.raises(ValueError):
        sf.glass_delta([1.0, 2.0], [2.0, 2.0])
