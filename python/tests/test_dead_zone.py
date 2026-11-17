"""Dead zone (ADR 0246)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_soft_threshold() -> None:
    x = np.random.default_rng(21).standard_normal(500)
    y = sf.dead_zone(x, 0.7)
    want = np.sign(x) * np.maximum(np.abs(x) - 0.7, 0.0)
    assert np.array_equal(y, want)


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.dead_zone(np.array([1 + 1j]), 0.5)
