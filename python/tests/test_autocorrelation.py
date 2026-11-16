"""Autocorrelation (conventions: Pulse shaping, Autocorrelation; ADR 0148)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

RNG = np.random.default_rng(148)
X = RNG.standard_normal(40) + 1j * RNG.standard_normal(40)


def test_matches_a_direct_two_sided_sum() -> None:
    n = X.size
    lags = range(-n + 1, n)
    direct = np.array(
        [sum(X[i + k] * np.conj(X[i]) for i in range(max(0, -k), min(n, n - k))) for k in lags]
    )
    r = sf.autocorrelation(X, scaling="none")
    np.testing.assert_allclose(r, direct[n - 1 :], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(np.conj(r[1:]), direct[n - 2 :: -1], rtol=1e-12, atol=1e-12)


def test_zero_lag_is_the_energy() -> None:
    assert sf.autocorrelation(X, 0, scaling="none")[0] == pytest.approx(np.sum(np.abs(X) ** 2))


def test_periodic_signal_peaks_at_its_period() -> None:
    x = np.tile(RNG.standard_normal(7), 20)
    r = sf.autocorrelation(x, 10, scaling="unbiased")
    assert int(np.argmax(r[1:])) + 1 == 7
