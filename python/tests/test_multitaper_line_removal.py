"""Multitaper line removal (conventions: Spectra, Multitaper line removal; ADR 0083)."""

import math

import numpy as np
import pytest

import signalforge as sf


def noisy_line(seed: int, n: int = 256) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return 2 * np.cos(2 * math.pi * 40 / n * t + 0.3) + 0.1 * rng.standard_normal(n)


def test_finds_the_line_and_restores_the_floor() -> None:
    x = noisy_line(1)
    r = sf.multitaper_line_removal(x, 1.0, 4.0, probability=1e-6)
    np.testing.assert_allclose(r.line_frequencies, [40 / 256])
    assert r.line_amplitudes[0] == pytest.approx(np.exp(0.3j), abs=0.02)  # A/2 e^{i phi}
    before = sf.multitaper_psd(x, 1.0, 4.0).psd[36:45]
    after = r.spectrum.psd[36:45]
    assert before.min() > 100 * 0.02 and after.max() < 4 * 0.02  # one-sided floor 2 sigma^2


def test_removal_is_subtraction_from_every_eigencoefficient() -> None:
    x = noisy_line(2, 64)
    m = 80
    r = sf.multitaper_line_removal(x, 1.0, 3.0, probability=1e-6, nfft=m)
    (b,) = np.rint(r.line_frequencies * m).astype(int)
    (mu,) = r.line_amplitudes
    n = np.arange(x.size)
    for v in sf.dpss_tapers(x.size, 3.0).tapers:
        expect = np.fft.fft(v * x, m)
        expect -= mu * np.fft.fft(v * np.exp(2j * math.pi * b * n / m), m)
        expect -= np.conj(mu) * np.fft.fft(v * np.exp(-2j * math.pi * b * n / m), m)
        np.testing.assert_allclose(np.fft.fft(v * r.residual, m), expect, atol=1e-12)


def test_one_line_per_peak_when_padded() -> None:
    n = 128
    t = np.arange(n)
    rng = np.random.default_rng(3)
    z = 1.5 * np.exp(2j * math.pi * 0.2137 * t) + 0.05 * rng.standard_normal(n)
    test = sf.harmonic_f_test(z, 1.0, 4.0, nfft=8 * n)
    assert np.sum(test.p_values < 1e-6) > 1  # several padded bins pass the threshold alone
    r = sf.multitaper_line_removal(z, 1.0, 4.0, probability=1e-6, nfft=8 * n)
    assert r.line_frequencies.size == 1
    assert r.line_frequencies[0] == pytest.approx(0.2137, abs=0.5 / (8 * n))


def test_no_lines_leaves_the_input() -> None:
    x = np.random.default_rng(4).standard_normal(50)
    r = sf.multitaper_line_removal(x, 2.0, 2.5, probability=1e-9, adaptive=True)
    assert r.line_frequencies.size == 0 and r.line_amplitudes.size == 0
    np.testing.assert_array_equal(r.residual, x)
    np.testing.assert_array_equal(r.spectrum.psd, sf.multitaper_psd(x, 2.0, 2.5, adaptive=True).psd)


def test_rejects() -> None:
    x = noisy_line(5, 32)
    for p in (0.0, 1.5, math.nan):
        with pytest.raises(ValueError):
            sf.multitaper_line_removal(x, 1.0, 2.0, probability=p)
    with pytest.raises(ValueError):
        sf.multitaper_line_removal(x, 1.0, 2.0, num_tapers=1)
    with pytest.raises(ValueError):
        sf.multitaper_line_removal(x, 1.0, 2.0, nfft=31)
    with pytest.raises(ValueError):
        sf.multitaper_line_removal(x + 0j, 1.0, 2.0, one_sided=True)
