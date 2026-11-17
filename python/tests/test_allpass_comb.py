"""Schroeder allpass section (ADR 0240)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_magnitude_response_is_flat() -> None:
    x = np.zeros(4096)
    x[0] = 1.0
    h = sf.allpass_comb(x, 37, 0.7)
    mag = np.abs(np.fft.fft(h))
    assert np.max(np.abs(mag - 1.0)) < 1e-9


def test_energy_is_preserved() -> None:
    x = np.random.default_rng(15).standard_normal(200)
    y = sf.allpass_comb(np.concatenate([x, np.zeros(5000)]), 11, -0.6)
    assert abs(np.sum(y**2) - np.sum(x**2)) < 1e-9
