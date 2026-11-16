"""Time weighting (conventions: Time weighting; ADR 0166)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_steady_tone_settles_to_its_mean_square() -> None:
    fs = 8000.0
    t = np.arange(int(2 * fs)) / fs
    y = sf.time_weighting(np.sqrt(2) * np.sin(2 * np.pi * 1000 * t), fs, 0.125)
    assert y[-1] == pytest.approx(1.0, abs=1e-3)
    assert np.all(y >= 0)


def test_one_time_constant_reaches_one_minus_one_over_e() -> None:
    fs, tau = 48000.0, 0.125
    y = sf.time_weighting(np.ones(int(tau * fs)), fs, tau)
    assert y[-1] == pytest.approx(1 - np.exp(-1), rel=1e-12)
