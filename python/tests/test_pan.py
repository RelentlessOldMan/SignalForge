"""Panner (ADR 0265)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_constant_power_keeps_power() -> None:
    x = np.ones(4)
    for p in np.linspace(-1, 1, 21):
        lr = sf.pan(x, float(p))
        assert np.allclose(lr.left**2 + lr.right**2, 1, rtol=0, atol=1e-15)


def test_linear_gains_sum_to_one() -> None:
    x = np.ones(4)
    for p in np.linspace(-1, 1, 21):
        lr = sf.pan(x, float(p), law="linear")
        assert np.allclose(lr.left + lr.right, 1, rtol=0, atol=1e-15)


def test_rejects_position_out_of_range() -> None:
    with pytest.raises(ValueError):
        sf.pan([1.0], -1.25)
