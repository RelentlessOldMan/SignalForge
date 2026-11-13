"""Phase noise: the Wiener walk's statistics against theory (conventions: Channel, Phase noise).
Seeded, so each check is deterministic; tolerances are several standard errors wide."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def _phase(y: np.ndarray) -> np.ndarray:
    return np.concatenate([[0.0], np.cumsum(np.angle(y[1:] * np.conj(y[:-1])))])


def test_increments_have_the_linewidths_variance() -> None:
    fs, linewidth, n = 1e6, 2000.0, 200_000
    sigma2 = 2 * math.pi * linewidth / fs
    phi = _phase(sf.phase_noise(np.ones(n, complex), linewidth, fs, seed=1))
    steps = np.diff(phi)
    assert np.mean(steps) == pytest.approx(0, abs=5 * math.sqrt(sigma2 / n))
    assert np.var(steps) == pytest.approx(sigma2, rel=5 * math.sqrt(2 / n))
    lag = 25
    assert np.var(phi[lag:] - phi[:-lag]) == pytest.approx(lag * sigma2, rel=0.05)


def test_the_mean_phasor_decays_as_theory_says() -> None:
    fs, linewidth, n, runs = 1000.0, 10.0, 40, 4000
    rng = np.random.default_rng(2)
    total = np.zeros(n, complex)
    for _ in range(runs):
        total += sf.phase_noise(np.ones(n, complex), linewidth, fs, seed=rng)
    sigma2 = 2 * math.pi * linewidth / fs
    want = np.exp(-np.arange(n) * sigma2 / 2)
    np.testing.assert_allclose(total.real / runs, want, atol=5 / math.sqrt(2 * runs))
    np.testing.assert_allclose(total.imag / runs, 0, atol=5 / math.sqrt(2 * runs))


def test_magnitude_and_first_sample_are_kept() -> None:
    x = np.array([0.3 + 0.4j, -2.0, 1j, 0.5 - 0.5j])
    y = sf.phase_noise(x, 1e4, 1e3, seed=3)
    np.testing.assert_allclose(np.abs(y), np.abs(x), rtol=1e-15)
    assert y[0] == x[0]
    assert sf.phase_noise([], 1.0, 1.0, seed=0).size == 0


def test_the_seed_decides_the_walk() -> None:
    x = np.ones(64, complex)
    a = sf.phase_noise(x, 100.0, 1e3, seed=4)
    np.testing.assert_array_equal(a, sf.phase_noise(x, 100.0, 1e3, seed=4))
    assert not np.array_equal(a, sf.phase_noise(x, 100.0, 1e3, seed=5))


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.phase_noise([1j], -1.0, 1.0, seed=0),
        lambda: sf.phase_noise([1j], math.nan, 1.0, seed=0),
        lambda: sf.phase_noise([1j], 1.0, 0.0, seed=0),
        lambda: sf.phase_noise([[1j]], 1.0, 1.0, seed=0),
        lambda: sf.phase_noise([1j], 1.0, 1.0, seed=-1),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
