"""PolyBLEP pulse-width modulation (ADR 0313)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_constant_duty_is_the_polyblep_square() -> None:
    y = sf.polyblep_pwm(np.full(200, 0.3), 8000.0, 123.0, 0.7, 0.2)
    assert np.array_equal(y, sf.polyblep_square(8000.0, 200, 123.0, 0.3, 0.7, 0.2))


def test_aliasing_is_far_below_the_naive_pwm() -> None:
    # A duty that swings 0.5 +- 0.2 once a second. Harmonic k carries sidebands about 1.3 k Hz
    # wide, so aliased energy is what lands more than 20 Hz from every true harmonic.
    n = np.arange(8000)
    d = 0.5 + 0.2 * np.sin(2 * np.pi * n / 8000)
    f = 311

    def aliased(y: np.ndarray) -> float:
        s = np.abs(np.fft.rfft(y)) ** 2
        keep = np.ones(s.size, dtype=bool)
        for k in range(0, 4000 // f + 1):
            keep[max(0, f * k - 20) : f * k + 21] = False
        return float(np.sum(s[keep]) / np.sum(s))

    assert aliased(sf.polyblep_pwm(d, 8000.0, f)) < aliased(sf.pwm(d, 8000.0, f)) / 10


def test_rejects_a_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.polyblep_pwm([0.5], 8000.0, -4001.0)
