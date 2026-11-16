"""Octave-band levels (conventions: Octave-band levels; ADR 0168)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_tone_at_a_band_center_lands_in_that_band() -> None:
    fs = 48000.0
    t = np.arange(int(fs)) / fs
    levels = sf.octave_band_levels(2 * np.sin(2 * np.pi * 1000 * t), fs, 1, 200.0, 5000.0)
    centers = sf.octave_bands(1, 200.0, 5000.0)[:, 1]
    assert levels[list(centers).index(1000.0)] == pytest.approx(2.0, rel=0.01)
    assert sorted(levels)[-2] < 0.1


def test_white_noise_band_powers_add_up() -> None:
    rng = np.random.default_rng(7)
    fs = 16000.0
    levels = sf.octave_band_levels(rng.standard_normal(64000), fs, 3, 400.0, 2500.0)
    rows = sf.octave_bands(3, 400.0, 2500.0)
    inside = (rows[-1, 2] - rows[0, 0]) / (fs / 2)
    assert levels.sum() == pytest.approx(inside, rel=0.05)
    assert np.all(levels > 0)
