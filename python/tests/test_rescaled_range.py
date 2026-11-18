"""Rescaled range and the Hurst exponent (ADR 0340)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

SCALES = [16, 32, 64, 128, 256, 512, 1024]


def test_white_noise_is_close_to_one_half() -> None:
    # Without the Anis-Lloyd correction the raw estimate sits a little above 0.5.
    x = np.random.default_rng(34).standard_normal(1 << 14)
    assert 0.5 <= sf.rescaled_range(x, SCALES).hurst <= 0.62


def test_a_random_walk_is_persistent() -> None:
    x = np.cumsum(np.random.default_rng(35).standard_normal(1 << 14))
    assert sf.rescaled_range(x, SCALES).hurst > 0.9


def test_scale_and_offset_change_nothing() -> None:
    x = np.random.default_rng(36).standard_normal(500)
    a = sf.rescaled_range(x, [5, 50, 500])
    b = sf.rescaled_range(3 * x - 2, [5, 50, 500])
    assert np.allclose(a.values, b.values, rtol=1e-12)


def test_rejects_a_constant_box() -> None:
    with pytest.raises(ValueError):
        sf.rescaled_range(np.ones(16), [4, 8])
