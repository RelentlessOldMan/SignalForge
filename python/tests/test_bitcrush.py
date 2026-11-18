"""Bitcrusher (ADR 0266)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_output_on_the_grid_and_in_range() -> None:
    rng = np.random.default_rng(34)
    x = rng.uniform(-1.5, 1.5, 1000)
    y = sf.bitcrush(x, 5, hold=4)
    k = y * 16
    assert np.array_equal(k, np.round(k))
    assert np.max(np.abs(k)) == 15
    assert np.all(y.reshape(-1, 4) == y.reshape(-1, 4)[:, :1])


def test_error_at_most_half_a_step_inside_full_scale() -> None:
    x = np.linspace(-0.9, 0.9, 501)
    assert np.max(np.abs(sf.bitcrush(x, 8) - x)) <= 2.0**-8


def test_rejects_one_bit() -> None:
    with pytest.raises(ValueError):
        sf.bitcrush([0.5], 1)
