"""Lomb-Scargle periodogram (conventions: Spectra, Lomb-Scargle periodogram; ADR 0059)."""

from __future__ import annotations

import numpy as np
import pytest

from signalforge import lomb_scargle, welch_psd

RNG = np.random.default_rng(59)
T = np.sort(RNG.uniform(0, 20, 80))
Y = np.cos(2 * np.pi * 0.4 * T + 0.3) + RNG.normal(0, 0.3, T.size)
F = np.linspace(0.05, 1.5, 60)


def test_peak_at_the_tone() -> None:
    p = lomb_scargle(T, Y, F)
    assert abs(F[np.argmax(p)] - 0.4) < F[1] - F[0]
    assert np.all((p >= 0) & (p <= 1 + 1e-12))


def test_order_of_samples_does_not_matter() -> None:
    k = RNG.permutation(T.size)
    assert np.allclose(lomb_scargle(T[k], Y[k], F), lomb_scargle(T, Y, F), rtol=1e-12, atol=1e-14)


def test_standard_ignores_scale_and_power_scales_by_its_square() -> None:
    assert np.allclose(lomb_scargle(T, 7 * Y, F), lomb_scargle(T, Y, F), rtol=1e-12)
    p1 = lomb_scargle(T, Y, F, normalization="power")
    assert np.allclose(lomb_scargle(T, 7 * Y, F, normalization="power"), 49 * p1, rtol=1e-12)


def test_center_removes_the_mean() -> None:
    assert np.allclose(lomb_scargle(T, Y + 5, F), lomb_scargle(T, Y, F), rtol=1e-9, atol=1e-12)
    # without centering, a large mean shows at the lowest frequencies
    raw = lomb_scargle(T, Y + 5, F, center=False, normalization="power")
    assert raw[0] > 10 * lomb_scargle(T, Y, F, normalization="power")[0]


def test_even_samples_match_the_periodogram_at_bins() -> None:
    # at a bin of even samples, P = |X[k]|^2 / N: half the one-sided rectangular periodogram
    n = 64
    x = RNG.normal(size=n)
    k = np.arange(1, n // 2)
    p = lomb_scargle(np.arange(n), x, k / n, normalization="power")
    w = welch_psd(x, 1.0, window="rectangular", detrend="constant")
    assert np.allclose(p, w.psd[1 : n // 2] / 2, rtol=1e-9)


def test_frequency_order_kept() -> None:
    p = lomb_scargle(T, Y, F)
    assert np.allclose(lomb_scargle(T, Y, F[::-1]), p[::-1], rtol=1e-12)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"times": [0, 1], "values": [1j, 2], "frequencies": [0.1]},
        {"times": [[0, 1]], "values": [[1, 2]], "frequencies": [0.1]},
        {"times": [0, 1], "values": [True, False], "frequencies": [0.1]},
        {"times": [0, 1], "values": ["a", "b"], "frequencies": [0.1]},
        {"times": [0, 1], "values": ["1", "2"], "frequencies": [0.1]},
        {"times": [0, 1], "values": [1, 2], "frequencies": [0.1], "normalization": "psd"},
    ],
)
def test_rejects(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        lomb_scargle(**kwargs)  # type: ignore[arg-type]
