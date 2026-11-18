"""Flanger (ADR 0272)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_mix_blends_dry_and_vibrato() -> None:
    rng = np.random.default_rng(39)
    x = rng.standard_normal(300)
    v = np.real(sf.vibrato(x, 6.0, 4.0, 2.0, 100.0))
    y = np.real(sf.flanger(x, 6.0, 4.0, 2.0, 100.0, 0.25))
    assert np.array_equal(y, x * 0.75 + v * 0.25)


def test_fixed_delay_notches() -> None:
    # delay 4 at mix 1/2 is (x[n] + x[n-4])/2, zero at fs/8
    period = np.cos(2 * np.pi * np.arange(8) / 8)
    period[4:] = -period[:4]  # exactly antiperiodic over 4 samples
    x = np.tile(period, 50)
    y = np.real(sf.flanger(x, 4.0, 0.0, 1.0, 8.0, 0.5))
    assert np.max(np.abs(y[4:])) == 0


def test_rejects_mix_above_one() -> None:
    with pytest.raises(ValueError):
        sf.flanger([1.0], 1.0, 0.5, 1.0, 8.0, 2.0)
