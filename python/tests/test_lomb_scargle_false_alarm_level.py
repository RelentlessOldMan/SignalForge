"""Lomb-Scargle false-alarm level (conventions: Spectra, false-alarm level; ADR 0082)."""

import itertools
import math

import numpy as np
import pytest

import signalforge as sf


def test_inverts_the_false_alarm_probability() -> None:
    for n, m, center in [(10, 1, True), (57, 30, True), (500, 4000, False), (4, 1, False)]:
        for p in (1e-12, 1e-6, 0.01, 0.5, 0.99):
            z = sf.lomb_scargle_false_alarm_level(p, n, num_frequencies=m, center=center)
            back = sf.lomb_scargle_false_alarm(z, n, num_frequencies=m, center=center)
            # near z = 1 the forward function's 1 - z keeps only the digits left after rounding z
            assert back == pytest.approx(p, rel=1e-9 if z < 1 - 1e-6 else 1e-3)


def test_falls_as_the_probability_rises() -> None:
    probabilities = (0, 0.01, 0.1, 1)
    levels = [sf.lomb_scargle_false_alarm_level(p, 40, num_frequencies=50) for p in probabilities]
    assert levels[0] == 1.0 and levels[-1] == 0.0
    assert all(a > b for a, b in itertools.pairwise(levels))


def test_white_noise_exceeds_it_at_the_stated_rate() -> None:
    # at one frequency the generalized value of Gaussian noise with the stated sigma is
    # Beta(1, (N - 3)/2) exactly
    rng = np.random.default_rng(82)
    n, trials, p = 20, 4000, 0.1
    z = sf.lomb_scargle_false_alarm_level(p, n)
    hits = 0
    for _ in range(trials):
        t = np.sort(rng.uniform(0, 10, n))
        sigma = rng.uniform(0.5, 2, n)
        y = 3 + sigma * rng.standard_normal(n)
        hits += sf.generalized_lomb_scargle(t, y, [0.37], uncertainties=sigma)[0] > z
    assert abs(hits / trials - p) < 4 * math.sqrt(p * (1 - p) / trials)


def test_rejects() -> None:
    for p in (-0.1, 1.5, math.nan):
        with pytest.raises(ValueError):
            sf.lomb_scargle_false_alarm_level(p, 10)
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_level(0.5, 3)
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_level(0.5, 2, center=False)
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_level(0.5, 10, num_frequencies=0)
