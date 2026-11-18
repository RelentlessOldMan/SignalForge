"""Crossfade (ADR 0263)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_constant_signal_stays_constant() -> None:
    x = np.full(50, 0.75)
    for shape in ("linear", "cosine"):
        y = sf.crossfade(x, x, 20, shape=shape)
        assert y.size == 80
        assert np.allclose(y, 0.75, rtol=0, atol=1e-15)


def test_ends_are_the_inputs() -> None:
    rng = np.random.default_rng(32)
    a, b = rng.standard_normal(30), rng.standard_normal(40)
    y = sf.crossfade(a, b, 10)
    assert np.array_equal(y[:20], a[:20])
    assert np.array_equal(y[30:], b[10:])


def test_rejects_overlap_longer_than_an_input() -> None:
    with pytest.raises(ValueError):
        sf.crossfade([1.0, 2.0], [3.0], 2)
