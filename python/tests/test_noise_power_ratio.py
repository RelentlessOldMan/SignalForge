"""Noise power ratio (conventions: Spectra, Noise power ratio; ADR 0118)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

N = 1024
LO, HI, NOTCH = 100, 300, (195, 205)


def notched_multitone() -> tuple[np.ndarray, np.ndarray]:
    """Bins LO..HI except the notch, Newman phases (written out here), unit cosines; returns the
    samples and the two-sided line coefficients on bins -HI..HI."""
    ks = [k for k in range(LO, HI + 1) if not NOTCH[0] <= k <= NOTCH[1]]
    phases = [math.pi * i * i / len(ks) for i in range(len(ks))]
    c = np.zeros(2 * HI + 1, dtype=np.complex128)  # index k + HI
    for k, ph in zip(ks, phases, strict=True):
        c[k + HI] = 0.5 * np.exp(1j * ph)
        c[-k + HI] = 0.5 * np.exp(-1j * ph)
    n = np.arange(N)
    x = sum(np.cos(2 * np.pi * k * n / N + ph) for k, ph in zip(ks, phases, strict=True))
    return np.asarray(x), c


def line_powers(c: np.ndarray, a3: float) -> np.ndarray:
    """One-sided power per bin of y = x + a3 x^3: the cube is the coefficients convolved three
    times (no FFT), folded mod N, then 2|c|^2 per bin above DC."""
    c3 = np.convolve(np.convolve(c, c), c)  # index k + 3*HI
    two = np.zeros(N, dtype=np.complex128)
    for i, v in enumerate(c3):
        two[(i - 3 * HI) % N] += a3 * v
    for i, v in enumerate(c):
        two[(i - HI) % N] += v
    p = 2 * np.abs(two[: N // 2 + 1]) ** 2
    p[0] /= 2
    p[N // 2] /= 2
    return p


@pytest.mark.parametrize("a3", [0.002, -0.01])
def test_a_cubic_fills_the_notch_as_its_expansion_says(a3: float) -> None:
    x, c = notched_multitone()
    d = sf.welch_psd(x + a3 * x**3, N, window="rectangular")
    p = line_powers(c, a3)
    band, notch = (LO - 0.5, HI + 0.5), (NOTCH[0] - 0.5, NOTCH[1] + 0.5)
    r = sf.noise_power_ratio(d.frequencies, d.psd, band, notch, span=(0, N / 2))
    inside = range(NOTCH[0], NOTCH[1] + 1)
    loaded = [k for k in range(LO, HI + 1) if k not in inside]
    want = 10 * math.log10(np.mean(p[loaded]) / np.mean(p[list(inside)]))
    assert r.npr_db == pytest.approx(want, abs=1e-8)
    assert r.loaded_density == pytest.approx(np.mean(p[loaded]), rel=1e-12)


def test_a_linear_load_leaves_the_notch_empty() -> None:
    x, _ = notched_multitone()
    d = sf.welch_psd(x, N, window="rectangular")
    r = sf.noise_power_ratio(d.frequencies, d.psd, (99.5, 300.5), (194.5, 205.5), span=(0, N / 2))
    assert r.npr_db > 200  # rounding only
    assert r.loaded_density == pytest.approx(0.5, rel=1e-12)  # each cosine's 1/2 over 1 Hz


def test_npr_falls_2_db_per_db_of_drive() -> None:
    # third-order distortion: notch density goes as drive^6, the load as drive^2
    x, _ = notched_multitone()
    got = []
    for a in (1e-3, 1e-2):
        d = sf.welch_psd(a * x + 0.01 * (a * x) ** 3, N, window="rectangular")
        got.append(sf.noise_power_ratio(d.frequencies, d.psd, (99.5, 300.5), (194.5, 205.5)).npr_db)
    assert got[0] - got[1] == pytest.approx(40, abs=1e-2)  # the load grows a little too


@pytest.mark.parametrize(
    ("band", "notch"),
    [((0, 10), (10, 11)), ((0, 10), (5, 4)), ((0, 10), (-1, 3)), ((0, 600), (5, 6))],
)
def test_bad_edges(band: tuple[float, float], notch: tuple[float, float]) -> None:
    f = np.arange(513.0)
    with pytest.raises(ValueError):
        sf.noise_power_ratio(f, np.ones(513), band, notch)
