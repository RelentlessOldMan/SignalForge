"""Feed-forward compressor (ADR 0257)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_steady_tone_settles_on_the_static_curve() -> None:
    n = np.arange(20000)
    x = 0.9 * np.sin(2 * np.pi * n / 40)
    y = sf.compress(x, -20.0, 4.0, 0.0, 0.9999)
    peak_db = 20 * np.log10(np.max(np.abs(y[10000:])))
    want = -20 + (20 * np.log10(0.9) + 20) / 4
    assert abs(peak_db - want) < 0.05


def test_quiet_signal_untouched() -> None:
    x = 0.01 * np.random.default_rng(30).standard_normal(500)
    assert np.array_equal(sf.compress(x, 0.0, 8.0, 0.5, 0.9), x)


def test_complex_keeps_phase() -> None:
    x = np.array([3 + 4j, -6 - 8j])
    y = sf.compress(x, 0.0, 2.0, 0.0, 0.0)
    assert y.dtype == np.complex128
    assert np.allclose(np.angle(y), np.angle(x), rtol=0, atol=1e-15)
