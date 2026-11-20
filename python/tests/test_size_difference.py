"""The size difference (ADR 0472)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_squared_mismatch_share() -> None:
    rng = np.random.default_rng(235)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.size_difference(t, d)
        assert v == pytest.approx(float(np.mean(t != d)) ** 2, abs=1e-15)
        assert v == sf.size_difference(d, t)
        assert 0.0 <= v <= 1.0


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.size_difference([0.0, 1.0], [1.0])
