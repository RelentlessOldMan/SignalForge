"""Sawtooth, square and triangle oscillators (ADR 0305)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _harmonics(x: np.ndarray, f0: int) -> np.ndarray:
    s = np.abs(np.fft.rfft(x)) / (x.size / 2)
    return np.asarray(s[f0 : 8 * f0 + 1 : f0])


def test_the_harmonics_follow_the_fourier_series() -> None:
    # 100 Hz at 64 kHz over one second: the naive forms are close to the series.
    k = np.arange(1, 9)
    saw = _harmonics(sf.sawtooth(64000.0, 64000, 100.0), 100)
    assert saw == pytest.approx(2 / (np.pi * k), abs=2e-3)
    sq = _harmonics(sf.square(64000.0, 64000, 100.0), 100)
    assert sq == pytest.approx(np.where(k % 2 == 1, 4 / (np.pi * k), 0), abs=2e-3)
    tri = _harmonics(sf.triangle(64000.0, 64000, 100.0), 100)
    assert tri == pytest.approx(np.where(k % 2 == 1, 8 / (np.pi * k) ** 2, 0), abs=2e-3)


def test_the_duty_sets_the_mean() -> None:
    assert np.mean(sf.square(8000.0, 8000, 100.0, duty=0.25, phase=1 / 160)) == pytest.approx(-0.5)


def test_rejects_an_infinite_phase() -> None:
    with pytest.raises(ValueError):
        sf.triangle(8000.0, 4, 100.0, phase=np.inf)
