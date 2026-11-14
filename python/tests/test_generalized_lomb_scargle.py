"""Generalized Lomb-Scargle (conventions: Spectra, Generalized Lomb-Scargle; ADR 0081)."""

import math

import numpy as np
import pytest

import signalforge as sf


def uneven(seed: int, n: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.sort(rng.uniform(0, 30, n))
    y = 4 + np.sin(2 * math.pi * 0.23 * t) + 0.5 * rng.standard_normal(n)
    return t, y, rng.uniform(0.3, 1.5, n)


def test_matches_a_weighted_least_squares_fit() -> None:
    t, y, sigma = uneven(1)
    f = np.array([0.07, 0.23, 0.41, 0.9])
    w = 1 / sigma**2
    mean = np.sum(w * y) / np.sum(w)
    chi0 = np.sum(w * (y - mean) ** 2)
    for fi, got in zip(f, sf.generalized_lomb_scargle(t, y, f, uncertainties=sigma), strict=True):
        om = 2 * math.pi * fi
        a = np.column_stack([np.cos(om * t), np.sin(om * t), np.ones_like(t)])
        coef = np.linalg.lstsq(a * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)[0]
        chi = np.sum(w * (y - a @ coef) ** 2)
        assert got == pytest.approx((chi0 - chi) / chi0, rel=1e-10)


def test_equals_the_classic_form_on_even_samples_at_bins() -> None:
    n = np.arange(32.0)
    x = 1.5 * np.cos(2 * math.pi * 3 / 32 * n + 0.4) + 0.3 * np.sin(2 * math.pi * 5 / 32 * n) + 2
    f = np.array([3, 5, 7, 11]) / 32
    for norm in ("standard", "power"):
        np.testing.assert_allclose(
            sf.generalized_lomb_scargle(n, x, f, normalization=norm),
            sf.lomb_scargle(n, x, f, normalization=norm),
            atol=1e-12,
        )


def test_floating_mean_keeps_the_power_the_classic_form_loses() -> None:
    # sampled mostly near the peaks: measured classic 0.960, generalized 1 (an exact fit)
    t = np.array([k + d for k in range(12) for d in (-0.05, 0.0, 0.05)] + [5.5, 8.5])
    y = 2 + np.cos(2 * math.pi * 0.9 * t)
    assert sf.generalized_lomb_scargle(t, y, [0.9])[0] == pytest.approx(1.0, abs=1e-12)
    assert sf.lomb_scargle(t, y, [0.9])[0] < 0.97


def test_scale_and_shift() -> None:
    t, y, sigma = uneven(2)
    f = np.array([0.1, 0.23, 0.5])
    base = sf.generalized_lomb_scargle(t, y, f, uncertainties=sigma)
    power = sf.generalized_lomb_scargle(t, y, f, uncertainties=sigma, normalization="power")
    np.testing.assert_allclose(sf.generalized_lomb_scargle(t, y, f, uncertainties=3 * sigma), base)
    np.testing.assert_allclose(
        sf.generalized_lomb_scargle(t, y, f, uncertainties=3 * sigma, normalization="power"),
        power / 9,
    )
    np.testing.assert_allclose(
        sf.generalized_lomb_scargle(t + 123.4, 5 * y - 7, f, uncertainties=sigma), base, rtol=1e-9
    )
    np.testing.assert_allclose(
        sf.generalized_lomb_scargle(t, y, f, uncertainties=np.ones_like(t)),
        sf.generalized_lomb_scargle(t, y, f),
    )


def test_rejects() -> None:
    t, y = [0.0, 1.0, 2.0], [1.0, 2.0, 0.5]
    with pytest.raises(ValueError):
        sf.generalized_lomb_scargle(t, y[:2], [0.3])
    with pytest.raises(ValueError):
        sf.generalized_lomb_scargle(t, y, [0.3], uncertainties=[1.0, 0.0, 1.0])
    with pytest.raises(ValueError):
        sf.generalized_lomb_scargle(t, y, [0.3], uncertainties=[1.0, 1.0])
    with pytest.raises(ValueError):
        sf.generalized_lomb_scargle(t, y, [-0.3])
    with pytest.raises(ValueError):
        sf.generalized_lomb_scargle(t, y, [0.3], normalization="psd")
    with pytest.raises(ValueError):
        sf.generalized_lomb_scargle(t, [2.0, 2.0, 2.0], [0.3])
