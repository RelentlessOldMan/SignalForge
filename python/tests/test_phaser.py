"""Phaser (ADR 0274)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_fixed_chain_matches_allpass_sections() -> None:
    rng = np.random.default_rng(42)
    x = rng.standard_normal(256)
    y = np.real(sf.phaser(x, 3, 1.5, 1.5, 2.0, 10.0, 1.0))
    sos = np.vstack([sf.allpass_first_order(1.5, 10.0)] * 3)
    assert np.allclose(y, np.real(sf.IirFilter(sos).process(x)), rtol=0, atol=1e-12)


def test_half_mix_notches_where_chain_inverts() -> None:
    # Two stages at fixed cutoff turn -pi at the cutoff, so mix 1/2 cancels a tone there.
    fs, f = 1000.0, 125.0
    n = np.arange(4000)
    x = np.cos(2 * np.pi * f * n / fs)
    y = np.real(sf.phaser(x, 2, f, f, 1.0, fs, 0.5))
    assert np.max(np.abs(y[2000:])) < 1e-9


def test_rejects_high_at_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.phaser([1.0], 2, 1.0, 4.0, 1.0, 8.0, 0.5)
