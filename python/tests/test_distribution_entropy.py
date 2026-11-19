"""Distribution entropy (ADR 0348)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_spreads_more_than_a_short_period() -> None:
    # A period-4 sequence has only a few distinct distances; noise fills the bins.
    noise = np.random.default_rng(51).standard_normal(200)
    periodic = np.tile([0.0, 1.0, 0.0, -1.0], 50)
    assert sf.distribution_entropy(periodic, 2, 64) < sf.distribution_entropy(noise, 2, 64)


def test_scale_and_offset_change_nothing() -> None:
    x = np.round(np.random.default_rng(52).standard_normal(200) * 32) / 32
    assert sf.distribution_entropy(4 * x + 8, 2, 16) == sf.distribution_entropy(x, 2, 16)


def test_a_constant_is_zero() -> None:
    assert sf.distribution_entropy(np.ones(10), 2) == 0.0


def test_rejects_one_bin() -> None:
    with pytest.raises(ValueError):
        sf.distribution_entropy([0.0, 1.0, 2.0], 1, 1)
