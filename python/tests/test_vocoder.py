"""Channel vocoder (ADR 0293)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_carrier_takes_the_modulator_spectrum() -> None:
    fs = 8000.0
    n = np.arange(16000)
    carrier = np.random.default_rng(56).standard_normal(n.size)
    modulator = np.sin(2 * np.pi * 400.0 * n / fs)
    y = sf.vocoder(carrier, modulator, 16, 100.0, 3500.0, 8.0, 0.99, 0.999, fs)
    s = np.abs(np.fft.rfft(y[8000:]))
    near = s[300:500].mean()
    far = s[2500:3500].mean()
    assert near > 10 * far


def test_one_band_is_the_scaled_band_times_the_envelope() -> None:
    rng = np.random.default_rng(57)
    c, m = rng.standard_normal(300), rng.standard_normal(300)
    f = 0.05 * (0.2 / 0.05) ** 0.5
    cb = sf.svf(c, f, 2.0, 1.0, output="bandpass") * 0.5
    mb = sf.svf(m, f, 2.0, 1.0, output="bandpass") * 0.5
    want = cb * sf.envelope_follower(mb, 0.3, 0.9)
    got = sf.vocoder(c, m, 1, 0.05, 0.2, 2.0, 0.3, 0.9, 1.0)
    assert got == pytest.approx(want, rel=1e-12, abs=1e-15)


def test_rejects_too_many_bands() -> None:
    with pytest.raises(ValueError):
        sf.vocoder([1.0], [1.0], 1001, 0.1, 0.2, 1.0, 0.5, 0.5, 1.0)
