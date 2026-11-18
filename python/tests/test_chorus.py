"""Chorus (ADR 0273)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_one_voice_is_the_flanger() -> None:
    rng = np.random.default_rng(40)
    x = rng.standard_normal(300)
    a = sf.chorus(x, 12.0, 5.0, 1.5, 200.0, 1, 0.4)
    b = sf.flanger(x, 12.0, 5.0, 1.5, 200.0, 0.4)
    assert np.array_equal(a, b)


def test_fixed_delay_voices_agree() -> None:
    rng = np.random.default_rng(41)
    x = rng.standard_normal(200)
    a = np.real(sf.chorus(x, 7.0, 0.0, 3.0, 100.0, 5, 1.0))
    assert np.allclose(a[7:], x[:-7], rtol=0, atol=1e-15)


def test_rejects_zero_voices() -> None:
    with pytest.raises(ValueError):
        sf.chorus([1.0], 2.0, 1.0, 1.0, 8.0, 0, 0.5)
