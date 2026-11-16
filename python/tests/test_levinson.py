"""Linear prediction by Levinson-Durbin (conventions: Pulse shaping, Linear prediction;
ADR 0149)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

RNG = np.random.default_rng(149)


def _ar2(n: int) -> np.ndarray:
    w = RNG.standard_normal(n)
    x = np.zeros(n)
    for i in range(2, n):
        x[i] = 0.75 * x[i - 1] - 0.5 * x[i - 2] + w[i]
    return x


def test_solves_the_toeplitz_system() -> None:
    x = RNG.standard_normal(64) + 1j * RNG.standard_normal(64)
    r = sf.autocorrelation(x, 6)
    lev = sf.levinson(r, 6)
    lags = np.arange(6)
    toeplitz = np.where(
        lags[:, None] >= lags[None, :],
        r[np.abs(lags[:, None] - lags[None, :])],
        np.conj(r[np.abs(lags[:, None] - lags[None, :])]),
    )
    np.testing.assert_allclose(
        lev.coefficients[1:], np.linalg.solve(toeplitz, -r[1:7]), rtol=1e-10, atol=1e-12
    )


def test_recovers_an_ar2_process() -> None:
    lev = sf.levinson(sf.autocorrelation(_ar2(100_000), 2), 2)
    np.testing.assert_allclose(lev.coefficients, [1.0, -0.75, 0.5], atol=0.02)
    assert lev.error == pytest.approx(1.0, rel=0.03)


def test_error_is_the_residual_mean_square() -> None:
    x = _ar2(500)
    lev = sf.levinson(sf.autocorrelation(x, 4), 4)
    residual = np.convolve(x, lev.coefficients)
    assert lev.error == pytest.approx(float(np.sum(residual**2)) / x.size, rel=1e-10)
