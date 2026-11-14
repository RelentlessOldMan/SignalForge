"""Thomson's harmonic F-test (conventions: Spectra, Harmonic F-test; ADR 0080)."""

import math

import numpy as np
import pytest

import signalforge as sf


def test_exact_bin_complex_line_gives_its_amplitude() -> None:
    # by hand: X_j = A U_j at the line's bin, so mu = A and the residual is rounding
    n = 64
    a = 1.5 - 0.5j
    r = sf.harmonic_f_test(a * np.exp(2j * math.pi * 5 * np.arange(n) / n), 1.0, 3.0)
    i = int(np.argmax(r.f_statistic))
    assert r.frequencies[i] == pytest.approx(5 / n)
    assert abs(r.amplitudes[i] - a) < 1e-12
    assert r.f_statistic[i] > 1e20
    assert r.num_tapers == 5
    assert r.frequencies.size == n  # complex input: the whole two-sided axis


def test_real_cosine_gives_half_its_amplitude() -> None:
    # measured: the -f image leaks 4.6e-6 into +f through the higher tapers at NW 4
    n = 1024
    x = 0.8 * np.cos(2 * math.pi * 100 * np.arange(n) / n + 0.7)
    r = sf.harmonic_f_test(x, 1.0, 4.0)
    assert r.frequencies.size == n // 2 + 1
    assert abs(r.amplitudes[100] - 0.4 * np.exp(0.7j)) < 1e-5


def test_p_values_are_uniform_under_white_noise() -> None:
    # measured over 20 runs of 1024: 1.07% below 0.01, 5.22% below 0.05, 49.96% below 0.5
    rng = np.random.default_rng(1)
    p = np.concatenate(
        [sf.harmonic_f_test(rng.standard_normal(1024), 1.0, 4.0).p_values[5:-5] for _ in range(20)]
    )
    for level in (0.05, 0.2, 0.5):
        assert np.mean(p < level) == pytest.approx(level, abs=0.015)


def test_finds_a_line_in_noise() -> None:
    rng = np.random.default_rng(2)
    n = 4096
    y = rng.standard_normal(n) + 0.3 * np.cos(2 * math.pi * 800 * np.arange(n) / n)
    r = sf.harmonic_f_test(y, 1.0, 4.0)
    assert int(np.argmin(r.p_values)) == 800
    assert r.p_values[800] < 1e-5
    assert abs(r.amplitudes[800]) == pytest.approx(0.15, abs=0.03)


def test_rejects() -> None:
    x = np.ones(16)
    with pytest.raises(ValueError):
        sf.harmonic_f_test(x, 1.0, 2.0, num_tapers=1)
    with pytest.raises(ValueError):
        sf.harmonic_f_test(x, 1.0, 1.0)  # default K = 1
    with pytest.raises(ValueError):
        sf.harmonic_f_test(np.array([]), 1.0, 1.0)
    with pytest.raises(ValueError):
        sf.harmonic_f_test(x, 1.0, 2.0, nfft=15)
    with pytest.raises(ValueError):
        sf.harmonic_f_test(x, 0.0, 2.0)
    with pytest.raises(ValueError):
        sf.harmonic_f_test(x, 1.0, 8.0)
