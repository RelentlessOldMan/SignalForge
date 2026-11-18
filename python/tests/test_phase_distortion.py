"""Phase-distortion oscillator (ADR 0319)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_middle_knee_is_a_cosine() -> None:
    y = sf.phase_distortion(8000.0, 200, 123.0, 0.5, 0.7, 0.1)
    t = 123.0 * (np.arange(200) / 8000.0) + 0.1
    assert np.allclose(y, -0.7 * np.cos(2 * np.pi * (t - np.floor(t))), rtol=0, atol=1e-14)


def test_a_smaller_knee_is_brighter() -> None:
    # One second at 8 kHz, 100 Hz: the share of power above the fundamental grows as the knee
    # moves away from 1/2.
    def overtones(knee: float) -> float:
        p = np.abs(np.fft.rfft(sf.phase_distortion(8000.0, 8000, 100.0, knee))) ** 2
        return float(p[150:].sum() / p.sum())

    shares = [overtones(k) for k in (0.5, 0.3, 0.1, 0.02)]
    assert shares[0] < 1e-20
    assert shares == sorted(shares)


@pytest.mark.parametrize("knee", [0.0, 1.0, -0.5, float("inf")])
def test_rejects_a_knee_outside_zero_to_one(knee: float) -> None:
    with pytest.raises(ValueError):
        sf.phase_distortion(8000.0, 4, 1000.0, knee)
