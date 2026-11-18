"""PolyBLEP triangle (ADR 0314)."""

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


@pytest.mark.parametrize("f", [311, 700, 1303])
def test_aliasing_is_far_below_the_naive_triangle(f: int) -> None:
    # One second at 8 kHz: 1 Hz bins; folded harmonics land between the true ones.
    naive = _aliased_fraction(sf.triangle(8000.0, 8000, float(f)), f)
    blep = _aliased_fraction(sf.polyblep_triangle(8000.0, 8000, float(f)), f)
    assert blep < naive / 10


def test_matches_the_naive_triangle_away_from_the_corners() -> None:
    naive = sf.triangle(8000.0, 64, 250.0, 1.0, 0.01)
    y = sf.polyblep_triangle(8000.0, 64, 250.0, 1.0, 0.01)
    u = (250.0 * np.arange(64) / 8000.0 + 0.01) % 1
    far = (np.minimum(u, 1 - u) > 1 / 32) & (np.abs(u - 0.5) > 1 / 32)
    assert np.allclose(y[far], naive[far], rtol=0, atol=1e-15)
    assert not np.allclose(y, naive)


def test_rejects_a_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.polyblep_triangle(8000.0, 4, 4001.0)
