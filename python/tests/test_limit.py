"""Lookahead peak limiter (ADR 0269)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_never_exceeds_threshold() -> None:
    rng = np.random.default_rng(37)
    x = 3 * rng.standard_normal(2000)
    for la in (0, 5, 40):
        y = sf.limit(x, 1.0, la, 0.99)
        assert np.max(np.abs(y)) <= 1.0 + 1e-15


def test_gain_drops_before_the_peak() -> None:
    x = np.full(20, 0.5)
    x[10] = 4.0
    y = np.real(sf.limit(x, 1.0, 3, 0.9))
    assert np.array_equal(y[:7], x[:7])
    assert np.allclose(y[7:11] / x[7:11], 0.25, rtol=0, atol=1e-16)


def test_rejects_release_of_one() -> None:
    with pytest.raises(ValueError):
        sf.limit([1.0], 1.0, 0, 1.0)
