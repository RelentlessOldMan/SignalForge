"""Transfer function H1 (conventions: Transfer function (H1); ADR 0193)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_fir_response_is_recovered_from_noise() -> None:
    rng = np.random.default_rng(40)
    x = rng.standard_normal(16384)
    h = np.array([0.5, 0.3, 0.1])
    y = np.convolve(x, h)[: x.size] + 0.01 * rng.standard_normal(x.size)
    t = sf.transfer_function(x, y, 1.0, nperseg=256)
    expected = np.fft.rfft(h, 256)
    assert np.allclose(t.response, expected, atol=0.02)
