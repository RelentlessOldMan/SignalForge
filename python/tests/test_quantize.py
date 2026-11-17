"""Uniform quantizer (ADR 0247)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_error_is_within_half_a_step() -> None:
    x = np.random.default_rng(22).uniform(-3, 3, 1000)
    y = sf.quantize(x, 0.1)
    assert np.max(np.abs(y - x)) <= 0.05 + 1e-15


def test_sqnr_of_a_full_scale_sine() -> None:
    bits = 10
    step = 2.0 / 2**bits
    n = np.arange(100000)
    x = np.sin(2 * np.pi * 0.0123457 * n)
    e = sf.quantize(x, step) - x
    sqnr = 10 * np.log10(0.5 / np.mean(e**2))
    assert abs(sqnr - (6.02 * bits + 1.76)) < 0.2
