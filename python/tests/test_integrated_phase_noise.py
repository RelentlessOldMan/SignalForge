"""Integrated phase noise and RMS jitter (conventions: Integrated phase noise; ADR 0109)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def lorentzian_band(f_lo: float, f_hi: float, linewidth: float, fs: float) -> float:
    # Wiener phase noise: S(f) = (1/fs)(1 - rho^2)/(1 - 2 rho cos w + rho^2), rho = exp(-pi dv/fs);
    # its integral is (1/pi) arctan(((1 + rho)/(1 - rho)) tan(pi f/fs))
    rho = math.exp(-math.pi * linewidth / fs)
    a = (1 + rho) / (1 - rho)

    def prim(f: float) -> float:
        return math.atan(a * math.tan(math.pi * f / fs)) / math.pi

    return prim(f_hi) - prim(f_lo)


def test_wiener_phase_noise_integrates_to_the_lorentzian() -> None:
    fs, dv, seg = 1e4, 10.0, 1024
    df = fs / seg
    x = sf.phase_noise(np.ones(1 << 18, dtype=complex), dv, fs, seed=11)
    lo, hi = 10.5 * df, 200.5 * df  # edges between bins, so the whole bins are the band
    r = sf.integrated_phase_noise(x, fs, lo, hi, nperseg=seg)
    want = 2 * lorentzian_band(lo, hi, dv, fs) / r.carrier_power  # both sides
    assert r.phase_rms**2 == pytest.approx(want, rel=0.05)
    assert r.integrated_dbc == pytest.approx(10 * math.log10(want), abs=0.2)


def test_small_sine_modulation_is_m_over_root_two() -> None:
    # the RMS of m sin(w_m n) is m/sqrt(2); jitter divides by 2 pi f_c
    n, kc, km, m = 1024, 300, 40, 1e-3
    t = np.arange(n)
    x = np.cos(2 * np.pi * kc * t / n + m * np.sin(2 * np.pi * km * t / n))
    r = sf.integrated_phase_noise(x, float(n), 20.5, 60.5)
    assert r.phase_rms == pytest.approx(m / math.sqrt(2), rel=1e-6)
    assert r.jitter_rms == pytest.approx(r.phase_rms / (2 * math.pi * kc), rel=1e-12)
    assert (r.f_lo, r.f_hi) == (20.5, 60.5)


def test_an_empty_band_gives_no_phase_error() -> None:
    # a coherent tone leaves only rounding outside its seven bins
    n = 1024
    x = np.cos(2 * np.pi * 100 * np.arange(n) / n)
    r = sf.integrated_phase_noise(x, float(n), 10.5, 50.5)
    assert r.phase_rms < 1e-6
    assert r.integrated_dbc < -120


def test_a_zero_carrier_frequency_has_infinite_jitter() -> None:
    n = 64
    x = np.ones(n, dtype=complex) + 1e-3 * np.exp(2j * np.pi * 10 * np.arange(n) / n)
    # a one-bin group (width 0) makes the centroid exactly the 0 Hz bin, not a rounding residue
    r = sf.integrated_phase_noise(x, float(n), 5.5, 20.5, width=0)
    assert r.carrier_frequency == 0.0
    assert r.jitter_rms == math.inf


@pytest.mark.parametrize(("lo", "hi"), [(math.nan, 8.0), (8.0, math.nan), (-1.0, 8.0)])
def test_bad_band(lo: float, hi: float) -> None:
    with pytest.raises(ValueError):
        sf.integrated_phase_noise(np.ones(64, dtype=complex), 64.0, lo, hi)
