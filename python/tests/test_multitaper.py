"""DPSS tapers and the multitaper PSD (conventions: Spectra, DPSS tapers, Multitaper PSD; ADR
0078)."""

import math

import numpy as np
import pytest

import signalforge as sf


def sinc_matrix(n: int, w: float) -> np.ndarray:
    d = np.arange(n)[:, None] - np.arange(n)[None, :]
    safe = np.where(d == 0, 1, d)
    return np.where(d == 0, 2 * w, np.sin(2 * math.pi * w * d) / (math.pi * safe))


@pytest.mark.parametrize(
    ("n", "nw", "k"), [(8, 1.0, 1), (31, 2.5, 4), (128, 4.0, 7), (257, 3.5, 6)]
)
def test_tapers_solve_the_concentration_problem(n: int, nw: float, k: int) -> None:
    t = sf.dpss_tapers(n, nw, k)
    a = sinc_matrix(n, nw / n)
    assert t.tapers.shape == (k, n)
    np.testing.assert_allclose(t.tapers @ t.tapers.T, np.eye(k), atol=1e-12)
    for v, lam in zip(t.tapers, t.concentrations, strict=True):
        np.testing.assert_allclose(a @ v, lam * v, atol=1e-11)
        assert lam == pytest.approx(v @ a @ v, abs=1e-12)
    assert np.all(np.diff(t.concentrations) < 0)


def test_default_count_and_concentration() -> None:
    t = sf.dpss_tapers(256, 4.0)
    assert t.tapers.shape[0] == 7  # 2NW - 1
    assert np.all(t.concentrations > 0.9)
    assert t.concentrations[0] > 1 - 1e-9
    assert sf.dpss_tapers(10, 0.4).tapers.shape[0] == 1


def test_sign_rule_and_symmetry() -> None:
    t = sf.dpss_tapers(40, 3.0, 5)
    mid = (40 - 1) / 2 - np.arange(40)
    for k, v in enumerate(t.tapers):
        if k % 2 == 0:
            assert v.sum() > 0
            np.testing.assert_allclose(v, v[::-1], atol=1e-12)
        else:
            assert mid @ v > 0
            np.testing.assert_allclose(v, -v[::-1], atol=1e-12)


def test_white_noise_level_and_parseval() -> None:
    rng = np.random.default_rng(5)
    fs, sigma = 500.0, 0.7
    x = sigma * rng.standard_normal(4096)
    p = sf.multitaper_psd(x, fs, 4.0)
    assert p.num_segments == 7
    assert p.enbw_hz == pytest.approx(8 / 4096 * fs)
    # one-sided density of white noise is 2 sigma^2 / fs
    assert np.mean(p.psd[1:-1]) == pytest.approx(2 * sigma**2 / fs, rel=0.02)
    # unit-norm tapers: the total is the mean over tapers of sum v^2 x^2, near the mean square
    total = np.sum(p.psd) * p.bin_width - (p.psd[0] + p.psd[-1]) * p.bin_width / 2
    assert total == pytest.approx(np.mean(x**2), rel=0.05)


def test_complex_two_sided_tone() -> None:
    n, fs = 512, 1000.0
    x = 2.0 * np.exp(2j * math.pi * 125.0 * np.arange(n) / fs)
    p = sf.multitaper_psd(x, fs, 3.0)
    assert not p.one_sided
    assert p.frequencies[np.argmax(p.psd)] == pytest.approx(125.0)
    assert np.sum(p.psd) * p.bin_width == pytest.approx(4.0, rel=1e-12)
    # nearly all of the tone's power A^2 lies within +-W of it (measured 0.996)
    band = np.abs(p.frequencies - 125.0) <= 3.0 / n * fs
    assert np.sum(p.psd[band]) * p.bin_width > 0.99 * 4.0


def test_leakage_near_the_band() -> None:
    # measured: the first taper at NW 4 leaks 4e-11 of the peak from 6 bins out and 2e-11
    # from 10, Hann 1e-6 and 5e-8; with all 2NW - 1 tapers the last one's 6% outside the band
    # puts it near the rectangular window
    n, f0 = 1024, 0.1013
    x = np.sin(2 * math.pi * f0 * np.arange(n))

    def leak(p: sf.SpectralDensity, bins: float) -> float:
        return float(np.max(p.psd[np.abs(p.frequencies - f0) > bins / n]) / np.max(p.psd))

    one = sf.multitaper_psd(x, 1.0, 4.0, num_tapers=1)
    hann = sf.welch_psd(x, 1.0, nperseg=n)
    for bins in (6, 10):
        assert leak(one, bins) < 1e-2 * leak(hann, bins)
    assert leak(sf.multitaper_psd(x, 1.0, 4.0), 6) < 1e-2


def test_nfft_pads_and_matches_frequencies() -> None:
    x = np.cos(0.4 * np.arange(50))
    p = sf.multitaper_psd(x, 2.0, 2.0, nfft=128)
    assert p.nfft == 128
    assert p.psd.size == 65
    assert p.bin_width == pytest.approx(2.0 / 128)
    np.testing.assert_allclose(p.frequencies, np.arange(65) * 2.0 / 128)


def test_rejects() -> None:
    x = np.ones(16)
    with pytest.raises(ValueError):
        sf.dpss_tapers(0, 0.5)
    for nw in (0.0, -1.0, 8.0, math.nan, math.inf):
        with pytest.raises(ValueError):
            sf.dpss_tapers(16, nw)
    for k in (0, 17):
        with pytest.raises(ValueError):
            sf.dpss_tapers(16, 2.0, k)
    with pytest.raises(ValueError):
        sf.multitaper_psd(np.ones(16, dtype=complex), 1.0, 2.0, one_sided=True)
    with pytest.raises(ValueError):
        sf.multitaper_psd(np.array([]), 1.0, 0.4)
    with pytest.raises(ValueError):
        sf.multitaper_psd(x, 1.0, 2.0, nfft=15)
    with pytest.raises(ValueError):
        sf.multitaper_psd(x, 0.0, 2.0)
    with pytest.raises(ValueError):
        sf.multitaper_psd(x, 1.0, 8.0)


def test_adaptive_is_a_fixed_point() -> None:
    # ADR 0079: each two-sided bin satisfies S = sum w_j S_j / sum w_j at its own weights
    rng = np.random.default_rng(9)
    n, fs, nw = 200, 10.0, 3.0
    x = np.sin(0.9 * np.arange(n)) + 0.01 * rng.standard_normal(n)
    t = sf.dpss_tapers(n, nw)
    eigen = np.array([np.abs(np.fft.fft(v * x)) ** 2 / fs for v in t.tapers])
    noise = np.sum(x**2) / n / fs
    s = np.fft.ifftshift(sf.multitaper_psd(x, fs, nw, one_sided=False, adaptive=True).psd)
    lam = t.concentrations[:, None]
    w = lam / (lam * s + (1 - lam) * noise) ** 2
    np.testing.assert_allclose(np.sum(w * eigen, axis=0) / np.sum(w, axis=0), s, rtol=1e-9)


def test_adaptive_cuts_the_leakage() -> None:
    # measured (ADR 0079): 3.6e-3 of the peak 6 bins out falls to 5.8e-7, 4.2e-5 at 50 to 2.9e-12
    n, f0 = 1024, 0.1013
    x = np.sin(2 * math.pi * f0 * np.arange(n))
    a = sf.multitaper_psd(x, 1.0, 4.0, adaptive=True)
    for bins, most in ((6, 1e-6), (50, 1e-11)):
        far = np.abs(a.frequencies - f0) > bins / n
        assert np.max(a.psd[far]) < most * np.max(a.psd)


def test_adaptive_noise_level_and_one_taper() -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(4096)
    a = sf.multitaper_psd(x, 1.0, 4.0, adaptive=True, one_sided=False)
    assert np.mean(a.psd) == pytest.approx(1.0, rel=0.02)
    one = sf.multitaper_psd(x[:300], 1.0, 3.0, num_tapers=1)
    np.testing.assert_array_equal(
        sf.multitaper_psd(x[:300], 1.0, 3.0, num_tapers=1, adaptive=True).psd, one.psd
    )
    np.testing.assert_array_equal(sf.multitaper_psd(np.zeros(9), 1.0, 2.0, adaptive=True).psd, 0)
