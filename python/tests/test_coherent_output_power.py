"""Coherent output power (conventions: Coherent output power; ADR 0198)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_parts_sum_to_the_output_psd_and_find_the_noise() -> None:
    rng = np.random.default_rng(47)
    x = rng.standard_normal(1 << 15)
    noise = 0.5 * rng.standard_normal(x.size)
    y = np.convolve(x, [1.0, 0.5])[: x.size] + noise
    r = sf.coherent_output_power(x, y, 2.0, nperseg=256)
    p = sf.welch_psd(y, 2.0, nperseg=256)
    assert np.allclose(r.coherent + r.noncoherent, p.psd)
    # white noise of variance 0.25 has one-sided PSD 2 * 0.25 / fs = 0.25 (bias ~ 1/K)
    assert abs(np.mean(r.noncoherent[1:-1]) - 0.25) < 0.03
