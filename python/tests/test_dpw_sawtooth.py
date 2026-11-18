"""DPW sawtooth (ADR 0317)."""

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
def test_aliasing_is_below_the_naive_sawtooth(f: int) -> None:
    # One second at 8 kHz: 1 Hz bins; folded harmonics land between the true ones.
    naive = _aliased_fraction(sf.sawtooth(8000.0, 8000, float(f)), f)
    dpw = _aliased_fraction(sf.dpw_sawtooth(8000.0, 8000, float(f)), f)
    assert dpw < naive / 4


def test_tracks_the_naive_sawtooth_at_a_low_pitch() -> None:
    # Away from the wrap y[n] is the naive value half a sample back: x[n] - 2 f / fs.
    y = sf.dpw_sawtooth(8000.0, 400, 20.0)
    naive = sf.sawtooth(8000.0, 400, 20.0)
    assert np.allclose(y[1:399], naive[1:399] - 2 * 20.0 / 8000.0 / 2, rtol=0, atol=1e-12)


def test_rejects_a_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.dpw_sawtooth(8000.0, 4, 4001.0)
