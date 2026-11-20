"""Mountford's coefficient (ADR 0452)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_not_negative() -> None:
    rng = np.random.default_rng(215)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [0.0, 1.0]
        v = sf.mountford_coefficient(t, d)
        assert v >= 0.0
        assert v == sf.mountford_coefficient(d, t)


def test_ignores_shared_zeros() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 0.0]
    d = [1.0, 0.0, 1.0, 1.0, 0.0]
    assert sf.mountford_coefficient(t + [0.0] * 5, d + [0.0] * 5) == sf.mountford_coefficient(t, d)


def test_rejects_records_that_agree_everywhere() -> None:
    with pytest.raises(ValueError):
        sf.mountford_coefficient([1.0, 0.0], [1.0, 0.0])
