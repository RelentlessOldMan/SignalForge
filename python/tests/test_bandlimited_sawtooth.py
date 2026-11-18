"""Band-limited sawtooth (ADR 0307)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_harmonics_stop_at_nyquist() -> None:
    # 700 Hz at 8 kHz over one second: 1 Hz bins, harmonics 1 to 5 below 4 kHz.
    y = sf.bandlimited_sawtooth(8000.0, 8000, 700.0)
    s = np.abs(np.fft.rfft(y)) / 4000
    for k in range(1, 6):
        assert s[700 * k] == pytest.approx(2 / (np.pi * k), abs=1e-9)
    s[[700 * k for k in range(1, 6)]] = 0
    assert np.max(s) < 1e-9


def test_a_low_note_is_close_to_the_naive_shape_away_from_the_jump() -> None:
    y = sf.bandlimited_sawtooth(48000.0, 480, 100.0, phase=0.25)
    naive = sf.sawtooth(48000.0, 480, 100.0, phase=0.25)
    assert np.max(np.abs(y - naive)[100:300]) < 0.01


def test_rejects_zero_frequency() -> None:
    with pytest.raises(ValueError):
        sf.bandlimited_sawtooth(8000.0, 4, 0.0)
