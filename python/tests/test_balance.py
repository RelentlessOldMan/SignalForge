"""Stereo balance (ADR 0277)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_centre_changes_nothing() -> None:
    rng = np.random.default_rng(45)
    a, b = rng.standard_normal(40), rng.standard_normal(40)
    y = sf.balance(a, b, 0.0)
    assert np.array_equal(y.left, a)
    assert np.array_equal(y.right, b)


def test_hard_right_mutes_left() -> None:
    y = sf.balance([1.0, 2.0], [3.0, 4.0], 1.0)
    assert y.left.tolist() == [0.0, 0.0]
    assert y.right.tolist() == [3.0, 4.0]


def test_rejects_position_out_of_range() -> None:
    with pytest.raises(ValueError):
        sf.balance([1.0], [1.0], 1.25)
