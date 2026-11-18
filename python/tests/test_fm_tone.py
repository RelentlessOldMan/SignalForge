"""Two-operator FM tone (ADR 0306)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def _bessel_j(k: int, x: float) -> float:
    """``J_k(x)`` from its power series, for small ``x``."""
    k = abs(k)
    return math.fsum(
        (-1) ** m * (x / 2) ** (2 * m + k) / (math.factorial(m) * math.factorial(m + k))
        for m in range(40)
    )


def test_the_sidebands_follow_bessel_functions() -> None:
    # Carrier 2000 Hz, modulator 200 Hz, one second at 16 kHz: 1 Hz bins, no wrap.
    i = 2.4
    y = sf.fm_tone(16000.0, 16000, 2000.0, 200.0, i)
    s = np.abs(np.fft.rfft(y)) / 8000
    for k in range(-6, 7):
        assert s[2000 + 200 * k] == pytest.approx(abs(_bessel_j(k, i)), abs=1e-9)


def test_rejects_an_infinite_index() -> None:
    with pytest.raises(ValueError):
        sf.fm_tone(8000.0, 4, 1000.0, 250.0, np.inf)
