"""Autocorrelation of a prediction-error filter (ADR 0220)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_levinson_inverts_it() -> None:
    a = sf.reflection_to_lpc([0.6 + 0.2j, -0.4, 0.3j, 0.5])
    r = sf.lpc_to_autocorrelation(a, 0.7, 4)
    fit = sf.levinson(r, 4)
    assert np.allclose(fit.coefficients, a, atol=1e-12)
    assert abs(fit.error - 0.7) < 1e-12


def test_matches_the_inverse_fft_of_the_model_spectrum() -> None:
    a = sf.reflection_to_lpc([0.5, -0.3, 0.2])
    s = 1.3 / np.abs(np.fft.fft(a, 4096)) ** 2
    r = np.fft.ifft(s).real[:6]
    assert np.allclose(sf.lpc_to_autocorrelation(a, 1.3, 5), r, atol=1e-12)
