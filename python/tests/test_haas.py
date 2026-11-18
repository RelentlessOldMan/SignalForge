"""Haas widener (ADR 0276)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_right_side_is_late_by_default() -> None:
    rng = np.random.default_rng(44)
    x = rng.standard_normal(50)
    y = sf.haas(x, 7)
    assert np.array_equal(y.left, x)
    assert np.array_equal(y.right[7:], x[:-7])
    assert not np.any(y.right[:7])


def test_left_side() -> None:
    y = sf.haas([1.0, 2.0, 3.0], 1, side="left")
    assert y.left.tolist() == [0.0, 1.0, 2.0]
    assert y.right.tolist() == [1.0, 2.0, 3.0]


def test_rejects_unknown_side() -> None:
    with pytest.raises(ValueError):
        sf.haas([1.0], 1, side="up")
