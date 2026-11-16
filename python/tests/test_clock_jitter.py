"""Sample clock jitter against the jitter SNR of a tone (conventions: Channel, Sample clock
jitter; ADR 0104)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize(("f", "rms"), [(0.05, 0.01), (0.05, 0.2), (0.2, 0.05), (0.2, 0.3)])
def test_tone_error_power_is_the_jitter_formula(f: float, rms: float) -> None:
    n = 20000
    x = np.exp(2j * math.pi * f * np.arange(n))
    y = sf.clock_jitter(x, rms, seed=11)
    inner = slice(16, n - 16)
    got = float(np.mean(np.abs(y - x)[inner] ** 2))
    # E|e^{jag} - 1|^2 = 2(1 - e^{-a^2/2}), a = 2 pi f rms: the Gaussian characteristic function
    a = 2 * math.pi * f * rms
    want = 2 * (1 - math.exp(-a * a / 2))
    assert got == pytest.approx(want, rel=0.05)


def test_the_offsets_are_white_with_the_given_spread() -> None:
    # a slow tone turns each read offset into a phase: arg(y/x) = 2 pi f d
    n, f, rms = 20000, 0.01, 0.1
    x = np.exp(2j * math.pi * f * np.arange(n))
    d = np.angle(sf.clock_jitter(x, rms, seed=4) / x)[16:-16] / (2 * math.pi * f)
    assert abs(d.mean()) < 4 * rms / math.sqrt(d.size)
    assert d.std() == pytest.approx(rms, rel=0.03)
    assert abs(np.corrcoef(d[:-1], d[1:])[0, 1]) < 0.03


def test_zero_rms_returns_the_input_and_seeds_repeat() -> None:
    x = np.array([1 + 2j, -0.5j, 3.0, 0.25 - 1j])
    np.testing.assert_array_equal(sf.clock_jitter(x, 0.0, seed=1), x)
    rng = np.random.default_rng(9)
    y = np.exp(0.3j * np.arange(50))
    a = sf.clock_jitter(y, 0.2, seed=rng)
    np.testing.assert_array_equal(sf.clock_jitter(y, 0.2, seed=np.random.default_rng(9)), a)
    assert not np.array_equal(sf.clock_jitter(y, 0.2, seed=10), a)
    assert sf.clock_jitter([], 0.4, seed=1).size == 0
    assert sf.clock_jitter(y, 0.5, seed=2, half_width=4).size == 50


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rms": -0.01},
        {"rms": 0.51},
        {"rms": math.nan},
        {"rms": math.inf},
        {"half_width": 0},
        {"seed": 1.5},
    ],
)
def test_bad_arguments(kwargs: dict[str, object]) -> None:
    args: dict[str, object] = {"rms": 0.1, "seed": 1} | kwargs
    with pytest.raises(ValueError):
        sf.clock_jitter(np.ones(4), **args)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        sf.clock_jitter(np.ones((2, 2)), 0.1, seed=1)
