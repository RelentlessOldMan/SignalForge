"""Auto-wah (ADR 0280)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_fixed_cutoff_is_the_unity_band_pass() -> None:
    rng = np.random.default_rng(49)
    x = rng.standard_normal(300)
    y = sf.auto_wah(x, 600.0, 600.0, 3.0, 0.5, 0.9, 8000.0, 1.0)
    bp = sf.svf(x, 600.0, 3.0, 8000.0, output="bandpass")
    assert np.allclose(y, bp / 3.0, rtol=0, atol=1e-12)


def test_louder_input_opens_the_filter() -> None:
    fs = 8000.0
    n = np.arange(4000)
    tone = np.sin(2 * np.pi * 2000.0 * n / fs)
    quiet = np.real(sf.auto_wah(0.05 * tone, 200.0, 2000.0, 4.0, 0.9, 0.99, fs, 1.0))
    loud = np.real(sf.auto_wah(1.0 * tone, 200.0, 2000.0, 4.0, 0.9, 0.99, fs, 1.0))
    tail = slice(3000, None)
    # Loud: envelope near 0.91, cutoff near the tone. Quiet: cutoff near 300 Hz.
    assert np.max(np.abs(loud[tail])) > 0.4
    assert np.max(np.abs(quiet[tail])) < 0.05 * 0.1


def test_rejects_low_above_high() -> None:
    with pytest.raises(ValueError):
        sf.auto_wah([1.0], 3.0, 2.0, 1.0, 0.5, 0.5, 8.0, 0.5)
