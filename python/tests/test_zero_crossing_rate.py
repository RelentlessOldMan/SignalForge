"""Zero-crossing rate (conventions: Zero-crossing rate; ADR 0146)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _sine(cycles: int, n: int) -> np.ndarray:
    return np.sin(2 * np.pi * cycles * np.arange(n) / n + 0.3)


def test_sine_crosses_twice_per_cycle() -> None:
    n = 1000
    assert sf.zero_crossing_rate(_sine(7, n)) == pytest.approx(14 / (n - 1), abs=1e-15)


def test_positive_scaling_leaves_it_unchanged() -> None:
    x = np.random.default_rng(146).standard_normal(500)
    assert sf.zero_crossing_rate(3.5 * x) == sf.zero_crossing_rate(x)


def test_complex_is_rejected() -> None:
    with pytest.raises(ValueError, match="real"):
        sf.zero_crossing_rate(np.array([1 + 1j, -1 - 1j]))
