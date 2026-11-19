"""Time irreversibility (ADR 0357)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_reversing_negates() -> None:
    x = np.round(np.random.default_rng(65).standard_normal(500) * 64) / 64
    assert sf.time_irreversibility(x[::-1], 2) == pytest.approx(
        -sf.time_irreversibility(x, 2), rel=1e-12
    )


def test_gaussian_noise_is_near_zero() -> None:
    x = np.random.default_rng(66).standard_normal(100_000)
    assert abs(sf.time_irreversibility(x)) < 0.03


def test_rejects_constant() -> None:
    with pytest.raises(ValueError):
        sf.time_irreversibility([1.0, 1.0, 1.0])
