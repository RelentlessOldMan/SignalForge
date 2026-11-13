import math
from typing import Any

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


def test_one_sided_span_counts_dc_and_nyquist_in_full() -> None:
    x = 1.0 + np.cos(2 * np.pi * np.arange(64) * 8 / 64) + 0.5 * np.cos(np.pi * np.arange(64))
    p = spectral.welch_psd(x, 64.0, window="rectangular")
    assert p.span == (0.0, 32.0)
    mean_power = float(np.mean(x * x))
    total = spectral.channel_power(p.frequencies, p.psd, 0, 32, span=p.span)
    assert total == pytest.approx(mean_power, rel=1e-12)
    assert spectral.channel_power(p.frequencies, p.psd, 0, 32) < mean_power
    obw = spectral.occupied_bandwidth(p.frequencies, p.psd, 1.0, span=p.span)
    assert (obw.lower, obw.upper) == (0.0, 32.0)


def test_two_sided_psd_has_no_span() -> None:
    assert spectral.welch_psd(np.ones(8, dtype=complex), 8.0).span is None


def test_kaiser_beta_limit() -> None:
    w = spectral.window("kaiser", 9, symmetric=True, beta=spectral.KAISER_MAX_BETA)
    assert np.all(np.isfinite(w)) and w[4] == 1.0
    for beta in (np.nextafter(spectral.KAISER_MAX_BETA, np.inf), np.inf, np.nan, -1.0):
        with pytest.raises(ValueError):
            spectral.window("kaiser", 9, beta=beta)


def test_welch_passes_beta_to_kaiser() -> None:
    x = np.arange(16.0)
    a = spectral.welch_psd(x, 1.0, window="kaiser", beta=6.0)
    w = spectral.window("kaiser", 16, beta=6.0)
    assert a.enbw_hz == pytest.approx(spectral.window_stats(w).enbw_bins / 16, rel=1e-14)


@pytest.mark.parametrize("bad", [2.5, 4.0, -1])
def test_counts_must_be_non_negative_integers(bad: float) -> None:
    with pytest.raises(ValueError):
        spectral.fft_frequencies(bad, 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        spectral.window("hann", bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        spectral.welch_psd(np.ones(8), 1.0, nperseg=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("complex_input", "nperseg", "noverlap", "name"),
    [
        (False, 16, None, "hann"),
        (False, 15, 3, "blackman"),
        (True, 16, 0, "kaiser"),
        (True, 9, 8, "hann"),
    ],
)
def test_spectrogram_rows_average_to_welch(
    complex_input: bool, nperseg: int, noverlap: int | None, name: str
) -> None:
    rng = np.random.default_rng(nperseg)
    x = rng.standard_normal(200) + (1j * rng.standard_normal(200) if complex_input else 0)
    beta = 6.0 if name == "kaiser" else None
    kw = {"noverlap": noverlap, "window": name, "beta": beta}
    s = spectral.spectrogram(x, 1e3, nperseg, **kw)  # type: ignore[arg-type]
    w = spectral.welch_psd(x, 1e3, nperseg=nperseg, **kw)  # type: ignore[arg-type]
    assert s.psd.shape == (w.num_segments, w.frequencies.size)
    assert np.allclose(s.psd.mean(axis=0), w.psd, rtol=1e-12, atol=0)
    assert np.array_equal(s.frequencies, w.frequencies)
    assert (s.num_segments, s.one_sided, s.bin_width, s.enbw_hz, s.span) == (
        w.num_segments,
        w.one_sided,
        w.bin_width,
        w.enbw_hz,
        w.span,
    )
    step = nperseg - (nperseg // 2 if noverlap is None else noverlap)
    assert np.allclose(s.times, (np.arange(s.num_segments) * step + nperseg / 2) / 1e3)


def test_spectrogram_tracks_a_frequency_step() -> None:
    fs, n = 1000.0, 64
    x = np.concatenate(
        [
            np.cos(2 * np.pi * 125 * np.arange(512) / fs),
            np.cos(2 * np.pi * 250 * np.arange(512) / fs),
        ]
    )
    s = spectral.spectrogram(x, fs, n, noverlap=0)
    peaks = s.frequencies[np.argmax(s.psd, axis=1)]
    assert np.all(peaks[:8] == 125) and np.all(peaks[8:] == 250)


def test_spectrogram_rejects_bad_arguments() -> None:
    x = np.ones(16)
    with pytest.raises(ValueError):
        spectral.spectrogram(x, 1.0, 4.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        spectral.spectrogram(x, 1.0, True)
    with pytest.raises(ValueError):
        spectral.spectrogram(x + 0j, 1.0, 4, one_sided=True)
    with pytest.raises(ValueError):
        spectral.spectrogram(x, 1.0, None)  # type: ignore[arg-type]


def test_a_bool_is_not_a_sample_rate() -> None:
    with pytest.raises(ValueError):
        spectral.welch_psd(np.zeros(8), True)
    with pytest.raises(ValueError):
        spectral.spectrogram(np.zeros(8), True, 4)


def test_acpr_of_on_bin_tones() -> None:
    # Unit tone at 8 Hz, 0.1 at -2 Hz and 0.01 at 18 Hz: -20 and -40 dBc at offset 10.
    n = np.arange(64)
    x = sum(a * np.exp(2j * np.pi * f * n / 64) for a, f in ((1, 8), (0.1, -2), (0.01, 18)))
    p = spectral.welch_psd(x, 64.0, window="rectangular")
    r = spectral.acpr(p.frequencies, p.psd, 8.0, 4.0, [10.0, 20.0])
    assert r.main_power == pytest.approx(1.0, rel=1e-12)
    assert r.lower_dbc[0] == pytest.approx(-20.0, abs=1e-9)
    assert r.upper_dbc[0] == pytest.approx(-40.0, abs=1e-9)
    assert r.lower_power[1] == pytest.approx(0.0, abs=1e-20)
    assert r.upper_power[1] == pytest.approx(0.0, abs=1e-20)
    assert r.lower_power[0] == pytest.approx(spectral.channel_power(p.frequencies, p.psd, -4, 0))


def test_acpr_of_flat_noise_is_the_bandwidth_ratio() -> None:
    f = np.arange(-50.0, 50.0)
    r = spectral.acpr(f, np.full(100, 2.0), 0.0, 10.0, [20.0], adjacent_bandwidth=5.0)
    assert r.main_power == pytest.approx(20.0)
    assert r.lower_dbc[0] == pytest.approx(10 * math.log10(0.5))
    assert r.upper_dbc[0] == pytest.approx(10 * math.log10(0.5))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"offsets": [60.0]},
        {"offsets": []},
        {"offsets": [[10.0]]},
        {"offsets": [-10.0]},
        {"bandwidth": math.inf},
        {"adjacent_bandwidth": 0.0},
        {"center": math.nan},
        {"center": 45.0, "bandwidth": 1.0, "offsets": [1.0]},
    ],
)
def test_acpr_rejects_bad_arguments(kwargs: dict[str, Any]) -> None:
    psd = np.where(np.arange(-50.0, 50.0) < 40, 1.0, 0.0)
    args: dict[str, Any] = {"center": 0.0, "bandwidth": 10.0, "offsets": [10.0]} | kwargs
    with pytest.raises(ValueError):
        spectral.acpr(np.arange(-50.0, 50.0), psd, **args)
