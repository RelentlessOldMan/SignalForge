"""Detrended fluctuation analysis (ADR 0332)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

SCALES = [16, 32, 64, 128, 256, 512]


def test_white_noise_has_alpha_one_half() -> None:
    x = np.random.default_rng(21).standard_normal(1 << 15)
    assert sf.detrended_fluctuation(x, SCALES).alpha == pytest.approx(0.5, abs=0.05)


def test_brownian_motion_has_alpha_three_halves() -> None:
    x = np.cumsum(np.random.default_rng(22).standard_normal(1 << 15))
    assert sf.detrended_fluctuation(x, SCALES).alpha == pytest.approx(1.5, abs=0.07)


def test_an_offset_changes_nothing() -> None:
    x = np.random.default_rng(23).standard_normal(1000)
    a = sf.detrended_fluctuation(x, [4, 10, 100])
    b = sf.detrended_fluctuation(x + 7.0, [4, 10, 100])
    assert np.allclose(a.fluctuations, b.fluctuations, rtol=1e-9)
    assert list(a.scales) == [4, 10, 100]


def test_rejects_a_constant() -> None:
    with pytest.raises(ValueError):
        sf.detrended_fluctuation(np.ones(16), [4, 8])
