"""Gammatone impulse response (conventions: Gammatone; ADR 0161)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_unit_gain_at_center_and_order4_bandwidth() -> None:
    fs, fc, n = 16000.0, 2000.0, 2000
    h = sf.gammatone(fc, fs, n)
    nfft = 1 << 18
    mag = np.abs(np.fft.rfft(h, nfft))
    f = np.arange(mag.size) * fs / nfft
    gain = abs(np.sum(h * np.exp(-2j * np.pi * fc / fs * np.arange(n))))
    assert gain == pytest.approx(1.0, rel=1e-12)
    above = f[mag >= 1 / math.sqrt(2)]
    want = 2 * math.sqrt(2**0.25 - 1) * 1.019 * float(sf.erb_bandwidth(fc))
    assert above[-1] - above[0] == pytest.approx(want, rel=0.02)
    assert abs(f[np.argmax(mag)] - fc) < 0.05 * want


def test_one_tap_of_order_four_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.gammatone(1000.0, 16000.0, 1)
