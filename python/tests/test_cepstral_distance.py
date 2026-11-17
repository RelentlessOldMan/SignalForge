"""Cepstral distance between AR models (ADR 0218)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_approaches_the_rms_log_spectral_difference() -> None:
    # Parseval: ln|1/A|^2 has Fourier coefficients c_n at n and -n, so the mean squared
    # difference of the two log spectra is 2 sum_{n>=1} |c_r[n] - c_t[n]|^2 for real models.
    ref = sf.reflection_to_lpc([0.6, -0.4, 0.3])
    test = sf.reflection_to_lpc([-0.5, 0.2])
    n = 1 << 14
    diff = np.log(np.abs(np.fft.fft(test, n)) ** 2) - np.log(np.abs(np.fft.fft(ref, n)) ** 2)
    rms2 = float(np.mean(diff**2))
    assert abs(sf.cepstral_distance(ref, test, 200) ** 2 - rms2 / 2) < 1e-10


def test_symmetric() -> None:
    a, b = [1.0, 0.5, 0.2], [1.0, -0.3]
    assert sf.cepstral_distance(a, b, 10) == sf.cepstral_distance(b, a, 10)
