"""Ping-pong delay (ADR 0275)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_impulse_bounces() -> None:
    y = sf.ping_pong_delay([1.0] + [0.0] * 12, 3, 0.5, 1.0)
    assert y.left.tolist() == [0, 0, 0, 1, 0, 0, 0, 0, 0, 0.25, 0, 0, 0]
    assert y.right.tolist() == [0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0.125]


def test_zero_feedback_is_one_echo_left() -> None:
    rng = np.random.default_rng(43)
    x = rng.standard_normal(100)
    y = sf.ping_pong_delay(x, 4, 0.0, 1.0)
    assert np.array_equal(y.left[4:], x[:-4])
    assert not np.any(y.right)


def test_rejects_unit_feedback() -> None:
    with pytest.raises(ValueError):
        sf.ping_pong_delay([1.0], 1, 1.0, 0.5)
