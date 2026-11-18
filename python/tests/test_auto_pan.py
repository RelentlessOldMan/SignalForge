"""Auto-panner (ADR 0270)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_pan_at_each_sample() -> None:
    x = np.array([0.5, -1.0, 0.25, 2.0, 1.0])
    lr = sf.auto_pan(x, 3.0, 0.8, 40.0)
    for n, v in enumerate(x):
        p = 0.8 * np.cos(2.0 * np.pi * 3.0 * (n / 40.0))
        one = sf.pan([v], float(p))
        assert abs(lr.left[n] - one.left[0]) < 1e-15
        assert abs(lr.right[n] - one.right[0]) < 1e-15


def test_constant_power() -> None:
    lr = sf.auto_pan(np.ones(500), 7.0, 1.0, 1000.0)
    assert np.allclose(lr.left**2 + lr.right**2, 1, rtol=0, atol=1e-15)


def test_rejects_depth_above_one() -> None:
    with pytest.raises(ValueError):
        sf.auto_pan([1.0], 1.0, 1.5, 8.0)
