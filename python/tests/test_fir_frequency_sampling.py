"""Frequency-sampling FIR design (conventions: FIR filters, Frequency-sampling design; ADR 0084)."""

import math
from collections.abc import Callable

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf


def amplitude(h: NDArray[np.float64], nu: NDArray[np.float64]) -> NDArray[np.float64]:
    """Zero-phase gain A(nu) = sum h[n] cos(2 pi nu t), t = n - (N - 1)/2."""
    t = np.arange(h.size) - (h.size - 1) / 2
    return np.asarray(np.cos(2 * math.pi * np.outer(nu, t)) @ h, dtype=np.float64)


def test_hits_the_samples_when_the_grid_matches_the_length() -> None:
    # rectangular window and L = N: the taps are one full period of the inverse DFT
    freqs, gains = [0, 0.1, 0.3, 0.5], [0.5, 1.5, 0.2, 0.0]
    h = sf.fir_frequency_sampling(24, freqs, gains, 1.0, window="rectangular", num_points=13)
    nu = np.arange(13) / 24
    np.testing.assert_allclose(amplitude(h, nu), np.interp(nu, freqs, gains), atol=1e-13)


def test_taps_are_exactly_symmetric() -> None:
    for n in (31, 32, 255):
        h = sf.fir_frequency_sampling(n, [0, 0.13, 0.21, 0.5], [1, 0.7, 0, 0], 1.0, window="hann")
        np.testing.assert_array_equal(h, h[::-1])


def test_long_design_approaches_the_target() -> None:
    h = sf.fir_frequency_sampling(201, [0, 0.1, 0.15, 0.5], [1, 1, 0, 0], 1.0, "kaiser", 8.0)
    assert np.max(np.abs(amplitude(h, np.linspace(0, 0.08, 50)) - 1)) < 1e-3
    assert np.max(np.abs(amplitude(h, np.linspace(0.17, 0.5, 50)))) < 1e-3


def test_linear_in_the_gains() -> None:
    f = [0, 0.2, 0.3, 0.5]
    g1, g2 = np.array([1, 1, 0, 0.0]), np.array([0.2, -0.5, 1, 3.0])
    both = sf.fir_frequency_sampling(17, f, 2.5 * g1 + g2, 1.0)
    each = 2.5 * sf.fir_frequency_sampling(17, f, g1, 1.0) + sf.fir_frequency_sampling(
        17, f, g2, 1.0
    )
    np.testing.assert_allclose(both, each, atol=1e-14)


def test_rejects() -> None:
    f, g = [0, 0.2, 0.3, 0.5], [1, 1, 0, 0]
    calls: list[Callable[[], object]] = [
        lambda: sf.fir_frequency_sampling(0, f, g, 1.0),
        lambda: sf.fir_frequency_sampling(11, [0, 0.2, 0.2, 0.5], g, 1.0),
        lambda: sf.fir_frequency_sampling(11, [0, 0.2, 0.3, 0.4], g, 1.0),
        lambda: sf.fir_frequency_sampling(11, f, [1, 1, 0], 1.0),
        lambda: sf.fir_frequency_sampling(10, f, [0, 0, 1, 1], 1.0),
        lambda: sf.fir_frequency_sampling(11, f, g, 1.0, num_points=5),
        lambda: sf.fir_frequency_sampling(11, f, g, 1.0, num_points=1),
        lambda: sf.fir_frequency_sampling(11, f, g, 1.0, beta=3.0),
    ]
    for call in calls:
        with pytest.raises(ValueError):
            call()


def anti_amplitude(h: NDArray[np.float64], nu: NDArray[np.float64]) -> NDArray[np.float64]:
    """A(nu) with H = -j e^(-j 2 pi nu c) A: A = sum h[n] sin(2 pi nu t), t = n - c."""
    t = np.arange(h.size) - (h.size - 1) / 2
    return np.asarray(np.sin(2 * math.pi * np.outer(nu, t)) @ h, dtype=np.float64)


def test_hilbert_turns_cos_into_sin() -> None:
    h = sf.fir_frequency_sampling(
        101, [0, 0.05, 0.45, 0.5], [0, 1, 1, 0], 1.0, "kaiser", 8.0, kind="hilbert"
    )
    n = np.arange(400)
    y = np.convolve(np.cos(2 * math.pi * 0.2 * n), h)[100:400]
    np.testing.assert_allclose(y, np.sin(2 * math.pi * 0.2 * (n[100:400] - 50)), atol=1e-3)


def test_differentiator_follows_the_slope() -> None:
    for n in (61, 60):
        h = sf.fir_frequency_sampling(
            n, [0, 0.4, 0.5], [1, 1, 0], 1.0, "kaiser", 8.0, kind="differentiator"
        )
        nu = np.linspace(0.01, 0.3, 30)
        np.testing.assert_allclose(anti_amplitude(h, nu), -2 * math.pi * nu, atol=2e-3)


def test_antisymmetric_taps_are_exact() -> None:
    for n in (31, 32):
        h = sf.fir_frequency_sampling(n, [0, 0.1, 0.5], [0, 1, 0], 1.0, kind="hilbert")
        np.testing.assert_array_equal(h, -h[::-1])
    assert (
        h.size == 32
        and sf.fir_frequency_sampling(31, [0, 0.5], [0, 0], 1.0, kind="hilbert")[15] == 0
    )


def test_rejects_unmeetable_antisymmetric_targets() -> None:
    f = [0, 0.2, 0.5]
    calls: list[Callable[[], object]] = [
        lambda: sf.fir_frequency_sampling(11, f, [0, 1, 0], 1.0, kind="lowpass"),
        lambda: sf.fir_frequency_sampling(1, f, [0, 1, 0], 1.0, kind="hilbert"),
        lambda: sf.fir_frequency_sampling(12, f, [1, 1, 1], 1.0, kind="hilbert"),
        lambda: sf.fir_frequency_sampling(11, f, [0, 1, 1], 1.0, kind="hilbert"),
        lambda: sf.fir_frequency_sampling(11, f, [1, 1, 1], 1.0, kind="differentiator"),
    ]
    for call in calls:
        with pytest.raises(ValueError):
            call()
