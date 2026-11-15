"""Bootstrap maxima for a Lomb-Scargle search (conventions: Spectra; ADR 0101)."""

import math

import numpy as np
import pytest

import signalforge as sf

RNG = np.random.default_rng(101)


def test_noise_agrees_with_baluev() -> None:
    # Baluev's estimate is close for small probabilities and errs high, never far low.
    t = np.sort(RNG.uniform(0, 30, 60))
    y = RNG.standard_normal(60)
    f = sf.lomb_scargle_frequencies(t, max_frequency=1.0)
    draws = 300
    peaks = sf.lomb_scargle_bootstrap(t, y, f, draws, seed=5)
    for level in (0.2, 0.25):
        p = sf.lomb_scargle_false_alarm_baluev(level, t, 1.0)
        se = math.sqrt(p * (1 - p) / draws)
        seen = float(np.mean(peaks > level))
        assert 0.5 * p - 4 * se < seen < p + 4 * se, (level, seen, p)


def test_a_strong_tone_is_above_every_draw() -> None:
    t = np.sort(RNG.uniform(0, 30, 50))
    y = np.sin(2 * np.pi * 0.37 * t) + 0.3 * RNG.standard_normal(50)
    f = sf.lomb_scargle_frequencies(t, max_frequency=1.0)
    observed = float(np.max(sf.lomb_scargle(t, y, f)))
    assert np.all(sf.lomb_scargle_bootstrap(t, y, f, 100, seed=1) < observed)


def test_shape_seed_and_bounds() -> None:
    t, y = np.arange(20.0), RNG.standard_normal(20)
    f = np.array([0.1, 0.2, 0.3])
    a = sf.lomb_scargle_bootstrap(t, y, f, 25, seed=3)
    assert a.shape == (25,)
    assert np.all((a >= 0) & (a <= 1))
    assert np.array_equal(a, sf.lomb_scargle_bootstrap(t, y, f, 25, seed=3))
    g = sf.lomb_scargle_bootstrap(t, y, f, 25, seed=np.random.default_rng(3))
    assert np.array_equal(a, g)


@pytest.mark.parametrize(("values", "center"), [([1.0, 1, 1, 2], True), ([0.0, 0, 0, 1], False)])
def test_draws_that_cannot_be_normalized_give_zero(values: list[float], center: bool) -> None:
    peaks = sf.lomb_scargle_bootstrap(
        [0, 1.3, 2.1, 3.7], values, [0.2, 0.4], 200, seed=2, center=center
    )
    assert np.any(peaks == 0)
    assert np.any(peaks > 0)


def test_a_constant_series_uncentered_repeats_its_peak() -> None:
    t, f = [0, 0.7, 1.9, 3.2], [0.13, 0.31]
    peak = float(np.max(sf.lomb_scargle(t, [2.0] * 4, f, center=False)))
    assert np.array_equal(
        sf.lomb_scargle_bootstrap(t, [2.0] * 4, f, 4, seed=9, center=False), [peak] * 4
    )


@pytest.mark.parametrize(
    ("values", "frequencies", "draws"),
    [
        ([1.0, 2, 3, 5], [0.2], 0),
        ([1.0, 2, 3, 5], [0.2], -1),
        ([1.0, 2, 3, 5], [], 3),
        ([2.0, 2, 2, 2], [0.2], 3),
        ([1.0, 2, 3], [0.2], 3),
        ([1.0, 2, math.nan, 5], [0.2], 3),
    ],
)
def test_rejects(values: list[float], frequencies: list[float], draws: int) -> None:
    with pytest.raises(ValueError):
        sf.lomb_scargle_bootstrap([0, 1, 2, 3], values, frequencies, draws, seed=1)
