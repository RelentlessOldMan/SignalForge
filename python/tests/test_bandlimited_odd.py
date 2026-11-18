"""Band-limited square and triangle (ADR 0309)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _check(y: np.ndarray, want: dict[int, float]) -> None:
    s = np.abs(np.fft.rfft(y)) / (y.size / 2)
    for k, amp in want.items():
        assert s[300 * k] == pytest.approx(amp, abs=1e-9)
        s[300 * k] = 0
    assert np.max(s) < 1e-9


def test_the_square_has_odd_harmonics_falling_as_one_over_k() -> None:
    # 300 Hz at 8 kHz over one second: odd harmonics 1 to 13 below 4 kHz.
    y = sf.bandlimited_square(8000.0, 8000, 300.0)
    _check(y, {k: 4 / (np.pi * k) for k in range(1, 14, 2)})


def test_the_triangle_has_odd_harmonics_falling_as_one_over_k_squared() -> None:
    y = sf.bandlimited_triangle(8000.0, 8000, 300.0, amplitude=2.0)
    _check(y, {k: 16 / (np.pi * k) ** 2 for k in range(1, 14, 2)})


def test_rejects_zero_frequency() -> None:
    with pytest.raises(ValueError):
        sf.bandlimited_triangle(8000.0, 4, 0.0)
