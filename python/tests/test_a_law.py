"""A-law companding (ADR 0249)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_round_trip() -> None:
    x = np.random.default_rng(24).uniform(-1, 1, 1000)
    assert np.allclose(sf.a_law_expand(sf.a_law_compress(x)), x, rtol=0, atol=1e-15)


def test_continuous_at_the_knee() -> None:
    a = 87.6
    k = 1 / a
    y = sf.a_law_compress([k * (1 - 1e-12), k, k * (1 + 1e-12)], a)
    assert np.max(np.abs(np.diff(y))) < 1e-12


def test_rejects_small_a() -> None:
    with pytest.raises(ValueError):
        sf.a_law_compress([0.5], 0.9)
