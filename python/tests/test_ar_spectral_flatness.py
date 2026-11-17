"""Spectral flatness of an AR model (ADR 0213)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_matches_the_sampled_model_spectrum() -> None:
    k = np.array([0.6 + 0.2j, -0.4, 0.3j, 0.1])
    a = sf.reflection_to_lpc(k)
    s = 1.0 / np.abs(np.fft.fft(a, 8192)) ** 2
    numeric = float(np.exp(np.mean(np.log(s))) / np.mean(s))
    assert abs(sf.ar_spectral_flatness(k) - numeric) < 1e-10


def test_white_noise_is_flat() -> None:
    assert sf.ar_spectral_flatness([0.0, 0.0]) == 1.0
