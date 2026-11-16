"""Power CCDF (conventions: Power CCDF; ADR 0119)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

N = 200_000
LEVELS = [-10.0, -3.0, 0.0, 3.0, 6.0, 9.0]


def tolerance(p: float, g: float) -> float:
    # five binomial sigmas, plus five sigmas of the sample mean moving the threshold
    return 5 * math.sqrt(p * (1 - p) / N) + 5 * g * p / math.sqrt(N)


def test_complex_gaussian_noise_is_exponential() -> None:
    rng = np.random.default_rng(119)
    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    r = sf.power_ccdf(x, LEVELS)
    for lv, got in zip(LEVELS, r.probabilities, strict=True):
        g = 10 ** (lv / 10)
        want = math.exp(-g)
        assert abs(got - want) <= tolerance(want, g) + 2 / N, lv


def test_real_gaussian_noise_is_chi_square_one() -> None:
    rng = np.random.default_rng(1190)
    r = sf.power_ccdf(rng.normal(size=N), LEVELS)
    for lv, got in zip(LEVELS, r.probabilities, strict=True):
        g = 10 ** (lv / 10)
        want = math.erfc(math.sqrt(g / 2))
        assert abs(got - want) <= tolerance(want, g) + 2 / N, lv


def test_a_complex_tone_never_exceeds_its_mean() -> None:
    n = np.arange(1000)
    x = 3 * np.exp(2j * np.pi * 0.123 * n)
    r = sf.power_ccdf(x, [0.01, 1.0, 3.0])
    np.testing.assert_array_equal(r.probabilities, 0)
    assert r.mean_power == pytest.approx(9, rel=1e-12)


def test_level_and_ccdf_are_inverses() -> None:
    rng = np.random.default_rng(11)
    x = rng.normal(size=5000) + 1j * rng.normal(size=5000)
    for q in (1e-3, 0.01, 0.1, 0.5):
        lv = sf.power_ccdf_level(x, q)
        # the threshold goes back through dB, so it is the same only up to rounding
        assert sf.power_ccdf(x, [lv + 1e-9]).probabilities[0] <= q
        assert sf.power_ccdf(x, [lv - 1e-9]).probabilities[0] > q


def test_level_below_one_sample_is_the_papr() -> None:
    rng = np.random.default_rng(12)
    x = rng.normal(size=777)
    assert sf.power_ccdf_level(x, 1e-4) == pytest.approx(sf.power_stats(x).papr_db, abs=1e-12)


@pytest.mark.parametrize("q", [0.0, 1.0, -0.1, math.nan])
def test_bad_probability(q: float) -> None:
    with pytest.raises(ValueError):
        sf.power_ccdf_level([1.0, 2.0], q)
