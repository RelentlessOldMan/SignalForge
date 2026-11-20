"""The shape difference (ADR 0473)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mismatch_share_less_the_squared_imbalance() -> None:
    rng = np.random.default_rng(236)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.shape_difference(t, d)
        k = float(np.mean(t - d))
        assert v == pytest.approx(float(np.mean(t != d)) - k * k, abs=1e-15)
        assert v == sf.shape_difference(d, t)
        assert 0.0 <= v <= 1.0


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.shape_difference([0.0, 1.0], [1.0])
