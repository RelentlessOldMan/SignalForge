"""Lomb-Scargle false-alarm probability and frequency grid (conventions: Spectra; ADR 0062)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

RNG = np.random.default_rng(62)


@pytest.mark.parametrize(("center", "times"), [(True, "even"), (False, "uneven")])
def test_single_frequency_survival_matches_noise(center: bool, times: str) -> None:
    # Centered needs even times at a bin for the Beta form to be exact; uncentered holds for any.
    n, trials = 24, 4000
    t = np.arange(n, dtype=float) if times == "even" else np.sort(RNG.uniform(0, 30, n))
    f = np.array([5 / n])
    z = np.array(
        [sf.lomb_scargle(t, RNG.standard_normal(n), f, center=center)[0] for _ in range(trials)]
    )
    for level in (0.1, 0.25, 0.4):
        p = sf.lomb_scargle_false_alarm(level, n, center=center)
        se = np.sqrt(p * (1 - p) / trials)
        assert abs(np.mean(z > level) - p) < 4 * se


def test_many_frequencies_is_monotone_and_bounded() -> None:
    p = [sf.lomb_scargle_false_alarm(0.3, 50, num_frequencies=m) for m in (1, 10, 100, 10**6)]
    assert p == sorted(p)
    assert 0 < p[0] < p[-1] <= 1


def test_tiny_single_probability_keeps_precision() -> None:
    p1 = 0.5**80
    assert sf.lomb_scargle_false_alarm(0.75, 83, num_frequencies=1000) == pytest.approx(
        1000 * p1, rel=1e-12
    )


def test_grid_feeds_the_periodogram() -> None:
    t = np.sort(RNG.uniform(0, 40, 60))
    f = sf.lomb_scargle_frequencies(t)
    span = t[-1] - t[0]
    assert f[0] == pytest.approx(1 / (5 * span))
    assert np.allclose(np.diff(f), f[0])
    assert f[-1] <= 60 / (2 * span) + 1e-12
    assert len(f) == int(5 * 60 / 2 + 1e-9)
    y = np.sin(2 * np.pi * f[40] * t)
    assert int(np.argmax(sf.lomb_scargle(t, y, f))) == 40


@pytest.mark.parametrize(
    "kwargs",
    [
        {"power": 1.01, "num_samples": 10},
        {"power": float("nan"), "num_samples": 10},
        {"power": 0.5, "num_samples": 3},
        {"power": 0.5, "num_samples": 2, "center": False},
        {"power": 0.5, "num_samples": 10, "num_frequencies": 0},
        {"power": 0.5, "num_samples": 10.0},
        {"power": True, "num_samples": 10},
    ],
)
def test_false_alarm_rejects(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        sf.lomb_scargle_false_alarm(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("times", "kwargs"),
    [
        ([1.0], {}),
        ([2.0, 2.0], {}),
        ([0.0, float("nan")], {}),
        ([0.0, 1.0], {"oversampling": 0.0}),
        ([0.0, 1.0], {"oversampling": float("inf")}),
        ([0.0, 1.0], {"max_frequency": 0.0}),
        ([0.0, 1.0], {"oversampling": 1e300, "max_frequency": 1e300}),
    ],
)
def test_frequencies_rejects(times: list[float], kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        sf.lomb_scargle_frequencies(times, **kwargs)
