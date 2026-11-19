"""Aggregated variance (ADR 0355)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_white_noise_is_near_one_half() -> None:
    x = np.random.default_rng(61).standard_normal(1 << 15)
    got = sf.aggregated_variance(x, [1, 2, 4, 8, 16, 32, 64])
    assert abs(got.hurst - 0.5) < 0.05


def test_a_random_walk_is_near_one() -> None:
    # A random walk is not stationary; its block means barely average out.
    x = np.cumsum(np.random.default_rng(62).standard_normal(1 << 14))
    assert sf.aggregated_variance(x, [4, 8, 16, 32]).hurst > 0.9


def test_rejects_block_means_that_do_not_vary() -> None:
    with pytest.raises(ValueError):
        sf.aggregated_variance([1.0, -1.0, 1.0, -1.0], [1, 2])
