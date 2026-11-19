"""Pettitt change-point test (ADR 0366)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_finds_a_level_shift() -> None:
    rng = np.random.default_rng(74)
    x = rng.standard_normal(300)
    x[180:] += 1.5
    got = sf.pettitt(x)
    assert 170 <= got.index <= 190
    assert got.p_value < 1e-6


def test_noise_is_not_significant_most_of_the_time() -> None:
    p = [sf.pettitt(np.random.default_rng(s).standard_normal(100)).p_value for s in range(100)]
    assert np.mean(np.array(p) < 0.05) < 0.15


def test_rejects_one_sample() -> None:
    with pytest.raises(ValueError):
        sf.pettitt([1.0])
