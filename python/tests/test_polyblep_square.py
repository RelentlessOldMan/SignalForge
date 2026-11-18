"""PolyBLEP square (ADR 0311)."""

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


@pytest.mark.parametrize(("f", "duty"), [(311, 0.5), (700, 0.5), (311, 0.3)])
def test_aliasing_is_far_below_the_naive_square(f: int, duty: float) -> None:
    # One second at 8 kHz: 1 Hz bins; folded harmonics land between the true ones.
    naive = _aliased_fraction(sf.square(8000.0, 8000, float(f), duty), f)
    blep = _aliased_fraction(sf.polyblep_square(8000.0, 8000, float(f), duty), f)
    assert blep < naive / 10


def test_matches_the_naive_square_away_from_the_edges() -> None:
    naive = sf.square(8000.0, 64, 250.0, 0.25, 1.0, 0.01)
    y = sf.polyblep_square(8000.0, 64, 250.0, 0.25, 1.0, 0.01)
    u = (250.0 * np.arange(64) / 8000.0 + 0.01) % 1
    far = (np.abs(u - 0.25) > 1 / 32) & (u > 1 / 32) & (u < 1 - 1 / 32)
    assert np.array_equal(y[far], naive[far])
    assert not np.array_equal(y, naive)


@pytest.mark.parametrize("duty", [-0.1, 1.1])
def test_rejects_a_duty_outside_zero_to_one(duty: float) -> None:
    with pytest.raises(ValueError):
        sf.polyblep_square(8000.0, 4, 1000.0, duty)


def test_rejects_a_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.polyblep_square(8000.0, 4, 4001.0)
