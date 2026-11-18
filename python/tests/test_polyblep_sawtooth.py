"""PolyBLEP sawtooth (ADR 0310)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _aliased_fraction(y: np.ndarray, f: int) -> float:
    s = np.abs(np.fft.rfft(y)) ** 2
    total = float(np.sum(s))
    s[0] = 0
    s[[f * k for k in range(1, 4000 // f + 1)]] = 0
    return float(np.sum(s)) / total


@pytest.mark.parametrize("f", [311, 700])
def test_aliasing_is_far_below_the_naive_sawtooth(f: int) -> None:
    # One second at 8 kHz: 1 Hz bins; folded harmonics land between the true ones.
    naive = _aliased_fraction(sf.sawtooth(8000.0, 8000, float(f)), f)
    blep = _aliased_fraction(sf.polyblep_sawtooth(8000.0, 8000, float(f)), f)
    assert blep < naive / 10


def test_rejects_a_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.polyblep_sawtooth(8000.0, 4, -4001.0)
