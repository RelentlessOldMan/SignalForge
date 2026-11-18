"""Noise gate (ADR 0255)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_mutes_noise_between_bursts() -> None:
    rng = np.random.default_rng(29)
    x = 0.01 * rng.standard_normal(3000)
    x[1000:1500] += np.sin(2 * np.pi * np.arange(500) / 50)
    y = sf.noise_gate(x, 0.1, hold=20)
    assert np.all(y[:1000] == 0)
    assert np.all(y[1600:] == 0)
    assert np.sum(y[1000:1500] ** 2) > 0.99 * np.sum(x[1000:1500] ** 2)


def test_complex_keeps_kind() -> None:
    y = sf.noise_gate(np.array([3 + 4j, 0.1j]), 1.0)
    assert y.dtype == np.complex128
    assert y[0] == 3 + 4j and y[1] == 0
