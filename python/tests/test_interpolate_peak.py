"""Peak interpolation (conventions: Spectra, Peak interpolation; ADR 0136)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

K = np.arange(16.0)


@pytest.mark.parametrize("mu", [6.5, 6.75, 7.0, 7.1, 7.49])
def test_db_fit_recovers_a_gaussian(mu: float) -> None:
    psd = 3.0 * np.exp(-((K - mu) ** 2) / 8)
    got = sf.interpolate_peak(K, psd, round(mu))
    assert got.frequency == pytest.approx(mu, abs=1e-12)
    assert got.height == pytest.approx(3.0, rel=1e-12)


@pytest.mark.parametrize("scale", ["db", "linear"])
def test_scaling_scales_the_height(scale: str) -> None:
    psd = np.array([0.4, 1.0, 2.5, 3.0, 1.2, 0.3])
    base = sf.interpolate_peak(K[:6], psd, 3, scale=scale)
    scaled = sf.interpolate_peak(K[:6], 7 * psd, 3, scale=scale)
    assert scaled.offset == pytest.approx(base.offset, abs=1e-12)
    assert scaled.height == pytest.approx(7 * base.height, rel=1e-12)


def test_hann_tone_between_bins() -> None:
    n, fs, f0 = 1024, 1024.0, 100.3
    t = np.arange(n) / fs
    x = np.cos(2 * np.pi * f0 * t) * np.hanning(n)
    psd = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(n, 1 / fs)
    got = sf.interpolate_peak(f, psd, int(np.argmax(psd)))
    assert abs(got.frequency - f0) < 0.05


def test_index_must_be_an_integer() -> None:
    with pytest.raises(ValueError):
        sf.interpolate_peak(K[:4], [1.0, 2.0, 3.0, 2.0], 2.0)  # type: ignore[arg-type]
