import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import spectral, waveforms


def direct_dft(x: NDArray[np.complex128]) -> NDArray[np.complex128]:
    n = np.arange(x.size)
    return np.asarray(np.exp(-2j * np.pi * np.outer(n, n) / x.size) @ x, dtype=np.complex128)


@pytest.mark.parametrize("n", [1, 2, 3, 7, 12, 16, 31])
def test_fft_matches_direct_dft_and_inverts(n: int) -> None:
    rng = np.random.default_rng(n)
    x = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    assert np.allclose(spectral.fft(x), direct_dft(x), atol=1e-12)
    assert np.allclose(spectral.ifft(spectral.fft(x)), x, atol=1e-12)


def test_fft_frequencies_match_numpy_order() -> None:
    for n in (1, 4, 5):
        assert np.allclose(spectral.fft_frequencies(n, 10.0), np.fft.fftfreq(n, 0.1))
        assert np.allclose(
            spectral.fft_frequencies(n, 10.0, shifted=True), np.fft.fftshift(np.fft.fftfreq(n, 0.1))
        )


def test_symmetric_windows_match_numpy() -> None:
    assert np.allclose(spectral.window("hann", 9, symmetric=True), np.hanning(9))
    assert np.allclose(spectral.window("hamming", 9, symmetric=True), np.hamming(9))
    assert np.allclose(spectral.window("blackman", 9, symmetric=True), np.blackman(9))
    assert np.allclose(spectral.window("kaiser", 9, symmetric=True, beta=8.6), np.kaiser(9, 8.6))


def test_periodic_window_is_symmetric_window_one_longer_truncated() -> None:
    for name in ("hann", "blackman_harris", "flattop"):
        assert np.allclose(
            spectral.window(name, 8), spectral.window(name, 9, symmetric=True)[:8], atol=1e-15
        )


def test_flattop_reads_tone_amplitude_between_bins() -> None:
    # A flat-top window reads a tone halfway between bins within a fraction of a percent.
    n, fs = 256, 256.0
    x = waveforms.tone(fs, n, 40.5, amplitude=1.0)
    w = spectral.window("flattop", n)
    peak = np.max(np.abs(spectral.fft(x * w))) / (n * spectral.window_stats(w).coherent_gain)
    assert peak == pytest.approx(1.0, abs=0.002)


def test_psd_integrates_to_mean_power_for_noise() -> None:
    rng = np.random.default_rng(1)
    x = (rng.standard_normal(1 << 16) + 1j * rng.standard_normal(1 << 16)) * np.sqrt(0.5 * 3.0)
    p = spectral.welch_psd(x, 1e6, nperseg=1024)
    assert np.sum(p.psd) * p.bin_width == pytest.approx(np.mean(np.abs(x) ** 2), rel=0.02)
    assert p.num_segments == (x.size - 1024) // 512 + 1
    assert p.enbw_hz == pytest.approx(1.5 * 1e6 / 1024)


def test_one_sided_and_two_sided_agree_for_real_input() -> None:
    rng = np.random.default_rng(2)
    x = rng.standard_normal(4096)
    one = spectral.welch_psd(x, 100.0, nperseg=256)
    two = spectral.welch_psd(x, 100.0, nperseg=256, one_sided=False)
    assert np.sum(one.psd) == pytest.approx(np.sum(two.psd), rel=1e-12)


def test_complex_input_cannot_be_one_sided() -> None:
    with pytest.raises(ValueError):
        spectral.welch_psd(np.ones(8, dtype=complex), 1.0, one_sided=True)


def test_obw_and_channel_power_of_a_flat_band() -> None:
    # Flat noise band from -10 to 10 Hz in a 100 Hz span: OBW 99% is 19.8 Hz.
    f = spectral.fft_frequencies(1000, 100.0, shifted=True)
    psd = np.where(np.abs(f) < 10, 1.0, 0.0)
    psd[np.isclose(np.abs(f), 10)] = 0.5  # the band edges fall on bin centers: half bins
    obw = spectral.occupied_bandwidth(f, psd)
    assert obw.bandwidth == pytest.approx(19.8, abs=1e-9)
    assert obw.lower == pytest.approx(-9.9, abs=1e-9)
    assert spectral.channel_power(f, psd, -10.05, 10.05) == pytest.approx(obw.total_power)
    assert spectral.channel_power(f, psd, -10.05, 10.05) == pytest.approx(20.0)
