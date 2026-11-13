"""Welch options: detrending is a projection, the median is unbiased for noise and resists bursts,
zero padding samples the same spectrum finer (conventions: Spectra, PSD)."""

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("detrend", ["constant", "linear"])
def test_detrending_ignores_the_removed_part(detrend: str) -> None:
    rng = np.random.default_rng(1)
    x = rng.standard_normal(96)
    n = np.arange(96)
    added = 3.0 + (0.2 * n if detrend == "linear" else 0.0)
    a = sf.welch_psd(x, 10, nperseg=16, detrend=detrend).psd
    b = sf.welch_psd(x + added, 10, nperseg=16, detrend=detrend).psd
    assert np.allclose(a, b, rtol=1e-9, atol=1e-12)
    raw = sf.welch_psd(x + added, 10, nperseg=16).psd
    assert raw[0] > 10 * b[0]


def test_complex_linear_detrend_removes_a_complex_line() -> None:
    rng = np.random.default_rng(2)
    x = rng.standard_normal(64) + 1j * rng.standard_normal(64)
    line = (1 - 2j) + (0.1 + 0.3j) * np.arange(64)
    a = sf.welch_psd(x, 1, nperseg=16, detrend="linear").psd
    b = sf.welch_psd(x + line, 1, nperseg=16, detrend="linear").psd
    assert np.allclose(a, b, rtol=1e-9, atol=1e-12)


@pytest.mark.parametrize("segments", [255, 256])
def test_median_is_unbiased_for_white_noise(segments: int) -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(64 * segments)
    med = sf.welch_psd(x, 1, nperseg=64, noverlap=0, window="rectangular", average="median")
    mean = sf.welch_psd(x, 1, nperseg=64, noverlap=0, window="rectangular")
    assert abs(np.mean(med.psd[1:-1]) / np.mean(mean.psd[1:-1]) - 1) < 0.03


def test_median_of_a_steady_tone_reads_one_over_the_bias_high() -> None:
    n = np.arange(64 * 15)
    x = np.cos(2 * np.pi * 0.125 * n)
    med = sf.welch_psd(x, 1, nperseg=64, noverlap=0, average="median").psd
    mean = sf.welch_psd(x, 1, nperseg=64, noverlap=0).psd
    b15 = sum(1 / i for i in range(8, 16))  # by hand: the conventions' b(K) for K = 15
    assert abs(med[8] * b15 / mean[8] - 1) < 1e-12


def test_median_resists_a_burst() -> None:
    n = np.arange(64 * 15)
    x = np.cos(2 * np.pi * 0.125 * n)
    x[64 * 7 : 64 * 7 + 4] += 50.0
    clean = sf.welch_psd(np.cos(2 * np.pi * 0.125 * n), 1, nperseg=64, noverlap=0, average="median")
    med = sf.welch_psd(x, 1, nperseg=64, noverlap=0, average="median").psd
    mean = sf.welch_psd(x, 1, nperseg=64, noverlap=0).psd
    far = slice(20, 30)
    assert np.max(med[far]) < 1e-3 * np.max(mean[far])
    assert abs(med[8] / clean.psd[8] - 1) < 0.01


def test_spectrogram_rows_average_to_the_detrended_psd() -> None:
    rng = np.random.default_rng(4)
    x = rng.standard_normal(80) + 0.05 * np.arange(80)
    s = sf.spectrogram(x, 1, 16, detrend="linear")
    w = sf.welch_psd(x, 1, nperseg=16, detrend="linear")
    assert np.allclose(np.mean(s.psd, axis=0), w.psd, rtol=1e-12, atol=1e-15)


@pytest.mark.parametrize(("detrend", "average"), [("quadratic", "mean"), ("none", "max"),
                                                 ("", "mean"), ("none", "")])  # fmt: skip
def test_bad_options(detrend: str, average: str) -> None:
    with pytest.raises(ValueError):
        sf.welch_psd([1.0, 2.0, 3.0, 4.0], 1, nperseg=2, detrend=detrend, average=average)


def test_spectrogram_bad_detrend() -> None:
    with pytest.raises(ValueError):
        sf.spectrogram([1.0, 2.0, 3.0, 4.0], 1, 2, detrend="cubic")


@pytest.mark.parametrize("one_sided", [True, False])
def test_padding_samples_the_same_spectrum_finer(one_sided: bool) -> None:
    rng = np.random.default_rng(6)
    x = rng.standard_normal(100)
    plain = sf.welch_psd(x, 8, nperseg=20, one_sided=one_sided)
    padded = sf.welch_psd(x, 8, nperseg=20, one_sided=one_sided, nfft=80)
    every_fourth = padded.psd[::4]  # bin 4k of 80 is bin k of 20 (shifted: both start at -fs/2)
    assert np.allclose(every_fourth, plain.psd, rtol=1e-10, atol=1e-14)
    assert np.allclose(padded.frequencies[::4], plain.frequencies, rtol=0, atol=1e-12)
    assert padded.nfft == 80 and plain.nfft == 20
    assert padded.bin_width == 8 / 80 and padded.enbw_hz == plain.enbw_hz


def test_padding_keeps_the_total_power() -> None:
    rng = np.random.default_rng(7)
    x = rng.standard_normal(64) + 1j * rng.standard_normal(64)
    for nfft in (16, 17, 50):
        d = sf.welch_psd(x, 3, nperseg=16, nfft=nfft)
        base = sf.welch_psd(x, 3, nperseg=16)
        assert abs(np.sum(d.psd) * d.bin_width / (np.sum(base.psd) * base.bin_width) - 1) < 1e-12


def test_nfft_below_nperseg_raises() -> None:
    with pytest.raises(ValueError):
        sf.welch_psd(np.ones(8), 1, nperseg=4, nfft=3)
    with pytest.raises(ValueError):
        sf.spectrogram(np.ones(8), 1, 4, nfft=3)
