"""Itakura-Saito distance between AR models (ADR 0217)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def _spectrum(a: np.ndarray, error: float, n: int) -> np.ndarray:
    return error / np.abs(np.fft.fft(a, n)) ** 2


def test_matches_the_sampled_spectra() -> None:
    ref = sf.reflection_to_lpc([0.6 + 0.2j, -0.4, 0.3j])
    test = sf.reflection_to_lpc([-0.5, 0.2 - 0.1j])
    ratio = _spectrum(ref, 1.3, 8192) / _spectrum(test, 0.7, 8192)
    numeric = float(np.mean(ratio - np.log(ratio) - 1))
    assert abs(sf.itakura_saito(ref, 1.3, test, 0.7) - numeric) < 1e-10


def test_equal_models_are_zero_apart() -> None:
    a = sf.reflection_to_lpc([0.5, -0.3, 0.2])
    assert abs(sf.itakura_saito(a, 2.0, a, 2.0)) < 1e-14
