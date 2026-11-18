"""Sidechain compressor (ADR 0278)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_self_keyed_is_the_compressor() -> None:
    rng = np.random.default_rng(46)
    x = rng.standard_normal(200)
    a = sf.duck(x, x, -10.0, 4.0, 0.3, 0.9, knee_db=3.0, makeup_db=1.0)
    b = sf.compress(x, -10.0, 4.0, 0.3, 0.9, knee_db=3.0, makeup_db=1.0)
    assert np.array_equal(a, b)


def test_quiet_key_leaves_samples() -> None:
    rng = np.random.default_rng(47)
    x = rng.standard_normal(50)
    y = sf.duck(x, np.full(50, 0.01), -6.0, 10.0, 0.5, 0.5)
    assert np.array_equal(y, x)


def test_rejects_complex_key() -> None:
    with pytest.raises(ValueError):
        sf.duck([1.0], [1j], 0.0, 2.0, 0.5, 0.5)
