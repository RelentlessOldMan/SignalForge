"""Bandlimited impulse train (ADR 0320)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_every_harmonic_below_nyquist_at_two_a_over_m() -> None:
    # One second at 8 kHz, 300 Hz: harmonics 1..13 (13 * 300 = 3900 < 4000), M = 27.
    y = sf.blit(8000.0, 8000, 300.0, 0.9)
    s = np.abs(np.fft.rfft(y)) / 8000
    lines = np.zeros(4001, dtype=bool)
    lines[300:4000:300] = True
    assert np.allclose(2 * s[lines], 2 * 0.9 / 27, rtol=1e-9)
    assert s[0] == pytest.approx(0.9 / 27, rel=1e-9)
    lines[0] = True
    assert np.max(s[~lines]) < 1e-12


def test_matches_the_cosine_sum_near_the_wrap() -> None:
    # Phases just either side of 0 and 1, where the closed form divides two small sines.
    y = sf.blit(8000.0, 6, 100.0, 1.0, 1 - 1e-7)
    t = 100.0 * (np.arange(6) / 8000.0) + (1 - 1e-7)
    u = t - np.floor(t)
    h = 39
    ref = (1 + 2 * np.cos(2 * np.pi * np.outer(u, np.arange(1, h + 1))).sum(axis=1)) / (2 * h + 1)
    assert np.allclose(y, ref, rtol=0, atol=1e-12)


def test_rejects_a_zero_frequency() -> None:
    with pytest.raises(ValueError):
        sf.blit(8000.0, 4, 0.0)
