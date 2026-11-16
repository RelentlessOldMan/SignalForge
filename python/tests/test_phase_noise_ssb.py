"""Single-sideband phase noise L(f) (conventions: Phase noise measurement; ADR 0108)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

BH = (0.35875, 0.48829, 0.14128, 0.01168)


def lorentzian_db(f: float, linewidth: float, fs: float) -> float:
    # Wiener phase noise: autocorrelation rho^|k|, rho = exp(-sigma^2/2), sigma^2 = 2 pi dv/fs
    rho = math.exp(-math.pi * linewidth / fs)
    w = 2 * math.pi * f / fs
    return 10 * math.log10((1 - rho**2) / (1 - 2 * rho * math.cos(w) + rho**2) / fs)


def test_wiener_phase_noise_follows_the_lorentzian() -> None:
    fs, dv = 1e4, 10.0
    x = sf.phase_noise(np.ones(1 << 18, dtype=complex), dv, fs, seed=7)
    offsets = [200.0, 500.0, 1000.0, 2000.0]
    r = sf.phase_noise_ssb(x, fs, offsets, nperseg=1024)
    # L is the sideband density over the carrier group's power; the density itself is S(f)
    got = r.l_dbc_hz + 10 * math.log10(r.carrier_power)
    want = [lorentzian_db(o, dv, fs) for o in offsets]
    np.testing.assert_allclose(got, want, atol=0.5)  # ~510 segments: about 0.13 dB per offset
    assert abs(r.carrier_frequency) < 2.0
    assert 0.5 < r.carrier_power < 1.0  # the group holds the Lorentzian's core, not its tails


def test_the_two_sidebands_are_averaged() -> None:
    # carrier 1 plus a line b at +k bins only: L = (b^2/ENBW)/2, 3 dB below one sideband
    n, k, b = 1024, 40, 1e-2
    t = np.arange(n)
    x = 1 + b * np.exp(2j * np.pi * k * t / n)
    a0, a1, a2, a3 = BH
    enbw = (a0**2 + (a1**2 + a2**2 + a3**2) / 2) / a0**2  # fs = n, so bins are 1 Hz
    r = sf.phase_noise_ssb(x, float(n), [float(k)])
    assert r.l_dbc_hz[0] == pytest.approx(10 * math.log10(b**2 / enbw / 2), abs=1e-9)
    assert r.carrier_power == pytest.approx(1.0, rel=1e-12)


def test_small_phase_modulation_is_half_the_phase_spectrum() -> None:
    # L ~ S_phi/2: a phase line m sin(w_m n) has S_phi power m^2/2, L power (m/2)^2 per sideband
    n, km, m = 1024, 50, 1e-3
    t = np.arange(n)
    x = np.cos(2 * np.pi * 200 * t / n + m * np.sin(2 * np.pi * km * t / n))
    a0, a1, a2, a3 = BH
    enbw = (a0**2 + (a1**2 + a2**2 + a3**2) / 2) / a0**2
    r = sf.phase_noise_ssb(x, float(n), [float(km)])
    assert r.l_dbc_hz[0] == pytest.approx(10 * math.log10((m / 2) ** 2 / enbw), abs=1e-5)
    assert r.carrier_frequency == pytest.approx(200.0, abs=1e-9)


def test_complex_upper_edge_is_exclusive() -> None:
    # the two-sided bins run -fs/2 ... fs/2 - df, so fc + o = fs/2 has no bin of its own
    x = np.ones(64, dtype=complex)
    sf.phase_noise_ssb(x, 64.0, [31.0])
    with pytest.raises(ValueError):
        sf.phase_noise_ssb(x, 64.0, [32.0])


@pytest.mark.parametrize("offsets", [[[8.0]], [math.nan]])
def test_bad_offsets(offsets: list[object]) -> None:
    with pytest.raises(ValueError):
        sf.phase_noise_ssb(np.ones(64, dtype=complex), 64.0, offsets)  # type: ignore[arg-type]
