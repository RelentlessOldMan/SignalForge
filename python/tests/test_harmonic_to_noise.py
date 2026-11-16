"""Harmonic-to-noise ratio (conventions: Spectra, Harmonic-to-noise ratio; ADR 0143)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

FREQS = np.arange(64) * 5.0
PSD = 1.0 + np.cos(FREQS / 7.0) ** 2


def test_scaling_psd_leaves_ratio_unchanged() -> None:
    a = sf.harmonic_to_noise(FREQS, PSD, 40.0, 5.0)
    b = sf.harmonic_to_noise(FREQS, 9.0 * PSD, 40.0, 5.0)
    assert b.ratio == pytest.approx(a.ratio, rel=1e-12)
    assert b.harmonic == pytest.approx(9.0 * a.harmonic, rel=1e-12)


def test_sine_in_white_noise() -> None:
    # A unit sine on a bin has power 1/2; white noise of variance 0.01 spreads 0.01 over the
    # one-sided spectrum, so the ratio is about 50 (17 dB). The noise sum over ~2048 bins has a
    # relative spread of about 2 %.
    n, fs, f0, sigma = 4096, 4096.0, 1000.0, 0.1
    rng = np.random.default_rng(143)
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * f0 * t) + sigma * rng.standard_normal(n)
    psd = 2 * np.abs(np.fft.rfft(x)) ** 2 / n**2
    got = sf.harmonic_to_noise(np.fft.rfftfreq(n, 1 / fs), psd, f0, 0.0)
    assert got.ratio == pytest.approx(0.5 / sigma**2, rel=0.1)
