"""Single-tone frequency by Kay's estimator (conventions: Single-tone frequency (Kay); ADR
0123)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("f", [-0.43, -0.2, -0.01, 0.0, 0.001, 0.17, 0.3333, 0.49])
def test_noiseless_tones_are_exact(f: float) -> None:
    n = np.arange(40)
    x = 2.5 * np.exp(1j * (2 * np.pi * f * n + 0.7))
    assert sf.kay_frequency(x, 1.0) == pytest.approx(f, abs=1e-13)


def test_amplitude_and_phase_change_nothing() -> None:
    n = np.arange(25)
    for amp, phase in [(1e-6, 0.0), (1.0, 2.0), (1e6, -3.0)]:
        x = amp * np.exp(1j * (2 * np.pi * 0.0123 * n + phase))
        assert sf.kay_frequency(x, 100.0) == pytest.approx(1.23, abs=1e-11)


def test_variance_is_near_the_crlb_at_high_snr() -> None:
    rng = np.random.default_rng(123)
    n_samples, trials, snr = 24, 4000, 10**3.0
    sigma = math.sqrt(1 / snr / 2)
    n = np.arange(n_samples)
    tone = np.exp(1j * 2 * np.pi * 0.1 * n)
    est = np.empty(trials)
    for t in range(trials):
        noise = sigma * (rng.normal(size=n_samples) + 1j * rng.normal(size=n_samples))
        est[t] = sf.kay_frequency(tone + noise, 1.0)
    crlb = 6 / ((2 * np.pi) ** 2 * snr * n_samples * (n_samples**2 - 1))
    assert float(np.mean(est)) == pytest.approx(0.1, abs=5 * math.sqrt(crlb / trials) + 1e-12)
    assert float(np.var(est)) / crlb == pytest.approx(1.0, abs=0.15)


def test_real_input_is_read_as_complex() -> None:
    assert sf.kay_frequency([1.0, 1.0, 1.0], 1.0) == 0.0
