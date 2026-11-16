"""Multiterm Lomb-Scargle against the generalized form, square waves and exact fits
(conventions: Spectra, Multiterm Lomb-Scargle; ADR 0103)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

rng = np.random.default_rng(103)
T = np.sort(rng.uniform(0, 30, 60))
Y = rng.standard_normal(60)
SIGMA = rng.uniform(0.5, 2.0, 60)
F = np.linspace(0.02, 1.5, 80)


@pytest.mark.parametrize("normalization", ["standard", "power"])
@pytest.mark.parametrize("weighted", [False, True])
def test_one_term_is_the_generalized_form(normalization: str, weighted: bool) -> None:
    sigma = SIGMA if weighted else None
    want = sf.generalized_lomb_scargle(T, Y, F, uncertainties=sigma, normalization=normalization)
    got = sf.lomb_scargle_multiterm(T, Y, F, 1, uncertainties=sigma, normalization=normalization)
    np.testing.assert_allclose(got, want, rtol=1e-10, atol=1e-13)


def test_square_wave_by_hand() -> None:
    t, y = np.arange(8.0), np.array([1.0] * 4 + [-1.0] * 4)
    part = (1 + math.sqrt(2) / 2) / 2
    for terms, want in ((1, part), (2, part), (3, 1.0), (4, 1.0), (6, 1.0)):
        assert sf.lomb_scargle_multiterm(t, y, [0.125], terms)[0] == pytest.approx(want, abs=1e-14)


def test_more_terms_explain_more() -> None:
    previous = np.zeros(F.size)
    for terms in range(1, 6):
        got = sf.lomb_scargle_multiterm(T, Y, F, terms, uncertainties=SIGMA)
        assert np.all(got >= previous - 1e-12)
        assert np.all((got >= 0) & (got <= 1 + 1e-12))
        previous = got


def test_harmonic_signal_fits_exactly_at_its_frequency() -> None:
    f0 = 0.23
    y = 1.5 + np.cos(2 * math.pi * f0 * T) + 0.6 * np.sin(6 * math.pi * f0 * T - 0.4)
    got = sf.lomb_scargle_multiterm(T, y, [f0, 1.3 * f0], 3)
    assert got[0] == pytest.approx(1.0, abs=1e-12)
    assert got[1] < 0.9
    # two terms miss the third harmonic's share
    assert sf.lomb_scargle_multiterm(T, y, [f0], 2)[0] < 0.9


def test_a_square_wave_peaks_at_its_frequency_with_harmonics() -> None:
    f0 = 0.31
    y = np.sign(np.sin(2 * math.pi * f0 * T)) + 0.1 * Y
    grid = np.linspace(0.05, 0.6, 400)
    for terms in (1, 3, 5):
        p = sf.lomb_scargle_multiterm(T, y, grid, terms)
        assert grid[np.argmax(p)] == pytest.approx(f0, abs=0.003)
    single = sf.lomb_scargle_multiterm(T, y, [f0], 1)[0]
    assert sf.lomb_scargle_multiterm(T, y, [f0], 5)[0] > single + 0.05


def test_shifting_every_time_changes_nothing() -> None:
    a = sf.lomb_scargle_multiterm(T, Y, F, 3, uncertainties=SIGMA)
    b = sf.lomb_scargle_multiterm(T + 12.5, Y, F, 3, uncertainties=SIGMA)
    np.testing.assert_allclose(a, b, rtol=1e-9, atol=1e-11)


def test_power_is_half_the_weighted_drop() -> None:
    std = sf.lomb_scargle_multiterm(T, Y, F, 2, uncertainties=SIGMA)
    power = sf.lomb_scargle_multiterm(T, Y, F, 2, uncertainties=SIGMA, normalization="power")
    w = 1 / SIGMA**2
    chi0 = np.sum(w * (Y - np.sum(w * Y) / np.sum(w)) ** 2)
    np.testing.assert_allclose(power, std * chi0 / 2, rtol=1e-12)


def test_empty_frequencies() -> None:
    assert sf.lomb_scargle_multiterm(T, Y, [], 2).size == 0


@pytest.mark.parametrize(
    "change",
    [
        {"terms": 0},
        {"terms": 1.5},
        {"terms": True},
        {"values": np.ones(60)},
        {"frequencies": [0.0]},
        {"frequencies": [math.nan]},
        {"times": T[:5]},
        {"uncertainties": -SIGMA},
        {"uncertainties": SIGMA[:3]},
        {"normalization": "psd"},
    ],
)
def test_bad_arguments(change: dict[str, object]) -> None:
    args: dict[str, object] = {"times": T, "values": Y, "frequencies": F, "terms": 2} | change
    with pytest.raises(ValueError):
        sf.lomb_scargle_multiterm(**args)  # type: ignore[arg-type]
