"""Baluev false-alarm probability for a Lomb-Scargle search (conventions: Spectra; ADR 0098)."""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest

import signalforge as sf

RNG = np.random.default_rng(98)


def _expected(z: float, t: np.ndarray, fmax: float, center: bool = True) -> float:
    d, h = (3, 1) if center else (2, 0)
    nk, nh = t.size - d, t.size - h
    # Gamma(nh/2)/Gamma((nh-1)/2) as an exact product: math.lgamma loses ~1e-11 at nh = 2e4.
    q = Fraction(1)
    for k in range(2 if nh % 2 == 0 else 3, nh, 2):
        q *= Fraction(k, k - 1)
    r = float(q) / math.sqrt(math.pi) if nh % 2 == 0 else float(q) * math.sqrt(math.pi) / 2
    g = math.sqrt(2 / nh) * r
    tau = fmax * math.sqrt(4 * math.pi * float(np.var(t))) * g
    tau *= (1 - z) ** ((nk - 1) / 2) * math.sqrt(nh * z / 2)
    return -math.expm1(math.log1p(-((1 - z) ** (nk / 2))) - tau)


def test_search_over_a_grid_is_close_to_noise() -> None:
    # Baluev's estimate is close for small probabilities and errs high, never far low.
    n, trials = 40, 600
    t = np.sort(RNG.uniform(0, 40, n))
    f = sf.lomb_scargle_frequencies(t, oversampling=5, max_frequency=0.5)
    peaks = np.array([sf.lomb_scargle(t, RNG.standard_normal(n), f).max() for _ in range(trials)])
    for level in (0.3, 0.35, 0.4):
        p = sf.lomb_scargle_false_alarm_baluev(level, t, 0.5)
        se = math.sqrt(p * (1 - p) / trials)
        assert 0.5 * p - 4 * se < np.mean(peaks > level) < p + 4 * se


@pytest.mark.parametrize("n", [5, 6, 101, 1000, 20001])
@pytest.mark.parametrize("center", [True, False])
def test_recurrence_matches_the_exact_product(n: int, center: bool) -> None:
    t = np.linspace(0, 7, n) ** 1.5
    for z in (0.001, 0.01, 0.2):
        got = sf.lomb_scargle_false_alarm_baluev(z, t, 3.0, center=center)
        assert got == pytest.approx(_expected(z, t, 3.0, center), rel=1e-11, abs=1e-300)


def test_is_monotone_and_bounded() -> None:
    t = np.sort(RNG.uniform(0, 10, 30))
    p = [sf.lomb_scargle_false_alarm_baluev(z, t, 2.0) for z in np.linspace(0, 1, 21)]
    assert p == sorted(p, reverse=True) and p[0] == 1.0 and p[-1] == 0.0
    q = [sf.lomb_scargle_false_alarm_baluev(0.3, t, f) for f in (0.1, 1.0, 10.0)]
    assert q == sorted(q) and all(0 <= x <= 1 for x in q)


def test_at_least_the_one_frequency_chance() -> None:
    t = np.arange(20.0)
    for z in (0.1, 0.4, 0.7):
        one = sf.lomb_scargle_false_alarm(z, 20)
        assert sf.lomb_scargle_false_alarm_baluev(z, t, 0.5) >= one


def test_shifting_the_times_changes_nothing() -> None:
    t = np.sort(RNG.uniform(0, 10, 25))
    a = sf.lomb_scargle_false_alarm_baluev(0.4, t, 1.5)
    assert sf.lomb_scargle_false_alarm_baluev(0.4, t + 1e3, 1.5) == pytest.approx(a, rel=1e-9)


@pytest.mark.parametrize(
    ("power", "times", "fmax", "center"),
    [
        (-0.1, [0, 1, 2, 3], 1.0, True),
        (1.01, [0, 1, 2, 3], 1.0, True),
        (math.nan, [0, 1, 2, 3], 1.0, True),
        (0.5, [0, 1, 2], 1.0, True),
        (0.5, [0, 1], 1.0, False),
        (0.5, [1, 1, 1, 1], 1.0, True),
        (0.5, [0, 1, 2, math.nan], 1.0, True),
        (0.5, [0, 1, 2, 3], 0.0, True),
        (0.5, [0, 1, 2, 3], -1.0, True),
        (0.5, [0, 1, 2, 3], math.inf, True),
    ],
)
def test_rejects(power: float, times: list[float], fmax: float, center: bool) -> None:
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_baluev(power, times, fmax, center=center)


@pytest.mark.parametrize("center", [True, False])
@pytest.mark.parametrize("z", [0.05, 0.3, 0.6, 0.9])
def test_level_inverts_the_probability(center: bool, z: float) -> None:
    t = np.sort(RNG.uniform(0, 20, 50))
    p = sf.lomb_scargle_false_alarm_baluev(z, t, 1.0, center=center)
    level = sf.lomb_scargle_false_alarm_level_baluev(p, t, 1.0, center=center)
    assert level == pytest.approx(z, rel=1e-9)


def test_level_is_the_edge_of_the_probability() -> None:
    t = np.sort(RNG.uniform(0, 20, 50))
    level = sf.lomb_scargle_false_alarm_level_baluev(0.01, t, 2.0)
    assert sf.lomb_scargle_false_alarm_baluev(level, t, 2.0) <= 0.01
    assert sf.lomb_scargle_false_alarm_baluev(np.nextafter(level, 0), t, 2.0) > 0.01


def test_level_ends() -> None:
    t = np.arange(30.0)
    assert sf.lomb_scargle_false_alarm_level_baluev(1.0, t, 1.0) == 0.0
    assert sf.lomb_scargle_false_alarm_level_baluev(0.0, t, 1.0) == 1.0
    p = [sf.lomb_scargle_false_alarm_level_baluev(q, t, 1.0) for q in (1e-6, 1e-3, 0.1, 0.5)]
    assert p == sorted(p, reverse=True)


@pytest.mark.parametrize("probability", [-0.1, 1.01, math.nan])
def test_level_rejects_probability(probability: float) -> None:
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_level_baluev(probability, [0, 1, 2, 3], 1.0)


def test_level_rejects_times() -> None:
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_level_baluev(0.1, [0, 1, 2], 1.0)
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm_level_baluev(0.1, [0, 1, 2, 3], 0.0)
