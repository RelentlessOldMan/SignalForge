"""Find tones (conventions: Spectra, Find tones; ADR 0137)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(12.0)
P = np.array([0.5, 3.0, 1.0, 4.0, 3.5, 2.0, 6.0, 0.2, 1.0, 0.3, 2.5, 1.5])


@pytest.mark.parametrize("scale", ["db", "linear"])
def test_tones_are_the_interpolated_top_peaks(scale: str) -> None:
    peaks = sorted(sf.spectral_peaks(F, P), key=lambda p: -p.prominence)[:3]
    got = sf.find_tones(F, P, 3, scale=scale)
    assert [t.index for t in got] == [p.index for p in peaks]
    for t, p in zip(got, peaks, strict=True):
        v = sf.interpolate_peak(F, P, p.index, scale=scale)
        assert (t.frequency, t.height, t.prominence) == (v.frequency, v.height, p.prominence)


def test_two_tones_in_noise() -> None:
    n, fs = 2048, 2048.0
    t = np.arange(n) / fs
    rng = np.random.default_rng(137)
    x = 2 * np.cos(2 * np.pi * 300.27 * t) + 0.5 * np.cos(2 * np.pi * 611.6 * t)
    x = (x + 1e-3 * rng.standard_normal(n)) * np.hanning(n)
    psd = np.abs(np.fft.rfft(x)) ** 2
    got = sf.find_tones(np.fft.rfftfreq(n, 1 / fs), psd, 2)
    assert abs(got[0].frequency - 300.27) < 0.05
    assert abs(got[1].frequency - 611.6) < 0.05


def test_count_must_be_an_integer() -> None:
    with pytest.raises(ValueError):
        sf.find_tones(F, P, 1.0)  # type: ignore[arg-type]
