"""Burg AR PSD (conventions: Burg AR PSD; ADR 0204)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_resolves_two_close_tones_that_yule_walker_blurs() -> None:
    n = np.arange(64)
    rng = np.random.default_rng(52)
    x = np.cos(2 * np.pi * 0.20 * n) + np.cos(2 * np.pi * 0.23 * n) + 0.01 * rng.standard_normal(64)
    d = sf.burg_psd(x, 1.0, 12, nfft=2000)
    f, p = d.frequencies, d.psd
    band = (f > 0.15) & (f < 0.28)
    peaks = [i for i in np.flatnonzero(band) if p[i] > p[i - 1] and p[i] > p[i + 1]]
    assert len(peaks) == 2
    assert abs(float(f[peaks[0]]) - 0.20) < 0.01 and abs(float(f[peaks[1]]) - 0.23) < 0.01


def test_complex_tone_peaks_at_its_frequency() -> None:
    n = np.arange(100)
    x = np.exp(2j * np.pi * -0.3 * n) + 0.1 * np.random.default_rng(53).standard_normal(100)
    d = sf.burg_psd(x, 1.0, 4, nfft=1000)
    assert abs(float(d.frequencies[int(np.argmax(d.psd))]) + 0.3) < 0.005
