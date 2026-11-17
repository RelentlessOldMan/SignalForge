"""Burg AR fit (conventions: Burg AR fit; ADR 0205)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def _ar1(n: int, phi: complex, seed: int, complex_noise: bool) -> np.ndarray:
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n) + (1j * rng.standard_normal(n) if complex_noise else 0)
    x = np.zeros(n, dtype=w.dtype)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + w[i]
    return x


def test_recovers_a_real_ar1_model() -> None:
    fit = sf.burg(_ar1(20000, 0.7, 54, False), 1)
    assert fit.coefficients.dtype == np.float64
    assert abs(float(fit.coefficients[1]) + 0.7) < 0.02
    assert abs(fit.error - 1.0) < 0.05


def test_recovers_a_complex_ar1_model() -> None:
    phi = 0.6 * np.exp(0.8j)
    fit = sf.burg(_ar1(20000, phi, 55, True), 1)
    assert np.iscomplexobj(fit.coefficients)
    assert abs(complex(fit.coefficients[1]) + phi) < 0.02
    assert abs(fit.error - 2.0) < 0.1


def test_psd_uses_the_fit() -> None:
    x = _ar1(200, 0.5, 56, False)
    fit = sf.burg(x, 3)
    d = sf.burg_psd(x, 2.0, 3, nfft=16, one_sided=False)
    two = fit.error / (2.0 * np.abs(np.fft.fft(fit.coefficients, 16)) ** 2)
    assert np.allclose(d.psd, np.fft.fftshift(two), rtol=1e-12, atol=0)
