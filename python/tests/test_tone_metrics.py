import math

import numpy as np
import pytest

from signalforge import measurements, spectral, waveforms


def test_group_powers_add_up_to_the_spectrum() -> None:
    n = np.arange(256)
    x = 0.2 + np.cos(2 * np.pi * 17.3 * n / 256) + 0.01 * np.cos(2 * np.pi * 34.6 * n / 256)
    m = measurements.tone_metrics(x, 256.0)
    d = spectral.welch_psd(x, 256.0, window="blackman_harris")
    total = m.signal_power + m.harmonic_power + m.noise_power + m.dc_power
    assert total == pytest.approx(float(np.sum(d.psd)) * d.bin_width, rel=1e-12)


def test_an_off_bin_tone_reads_its_power_and_frequency() -> None:
    fs, n = 48000.0, 1024
    f = 100.3 * fs / n
    x = waveforms.tone(fs, n, f, amplitude=0.5, complex=False)
    m = measurements.tone_metrics(x, fs)
    assert m.signal_power == pytest.approx(0.125, rel=1e-6)
    assert m.fundamental_frequency == pytest.approx(f, abs=0.01 * fs / n)


def test_white_noise_sets_the_snr() -> None:
    rng = np.random.default_rng(7)
    n = np.arange(8192)
    sigma = 0.01
    x = np.cos(2 * np.pi * 1000.5 * n / 8192) + sigma * rng.standard_normal(n.size)
    m = measurements.tone_metrics(x, 8192.0, num_harmonics=0)
    # the groups take 2 x 9 of the 4097 bins, so the noise is a little under sigma^2
    assert m.snr_db == pytest.approx(10 * math.log10(0.5 / sigma**2), abs=0.5)
    assert m.thd_db == -math.inf
    assert m.sinad_db == m.snr_db


def test_the_default_kaiser_width_is_the_main_lobe() -> None:
    n = np.arange(128)
    x = np.cos(2 * np.pi * 30 * n / 128) + 1e-3 * np.cos(2 * np.pi * 47 * n / 128)
    for beta, w in ((0.0, 1), (8.6, 3), (20.0, 7)):
        a = measurements.tone_metrics(x, 128.0, window="kaiser", beta=beta)
        b = measurements.tone_metrics(x, 128.0, window="kaiser", beta=beta, width=w)
        assert a == b


def test_complex_input_is_two_sided() -> None:
    x = waveforms.tone(64.0, 64, -12.0, amplitude=0.5) + 0.01 * waveforms.tone(64.0, 64, 20.0)
    m = measurements.tone_metrics(x, 64.0, window="hann", num_harmonics=1)
    assert m.fundamental_frequency == pytest.approx(-12.0)
    assert m.signal_power == pytest.approx(0.25)
    assert m.harmonic_power == pytest.approx(0.0, abs=1e-20)  # -24 Hz holds nothing
    assert m.noise_power == pytest.approx(1e-4)


@pytest.mark.parametrize(
    "kw",
    [
        {"width": True},
        {"width": 1.0},
        {"num_harmonics": 2.0},
        {"fundamental": True},
        {"fundamental": math.inf},
        {"window": "triangle"},
        {"window": "hann", "beta": 2.0},
    ],
)
def test_bad_arguments(kw: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        measurements.tone_metrics(np.cos(np.arange(32) * 1.2), 32.0, **kw)  # type: ignore[arg-type]


def test_sfdr_takes_the_strongest_spur_and_never_dc() -> None:
    n = np.arange(1024)
    x = 0.5 + np.cos(2 * np.pi * 100 * n / 1024) + 0.03 * np.cos(2 * np.pi * 200 * n / 1024)
    x += 0.001 * np.cos(2 * np.pi * 371.4 * n / 1024)
    s = measurements.sfdr(x, 1024.0, num_spurs=2)
    assert s.carrier_frequency == pytest.approx(100.0)
    assert s.spur_frequencies[0] == pytest.approx(200.0)
    assert s.sfdr_db == pytest.approx(-20 * math.log10(0.03), abs=1e-9)
    assert s.spur_frequencies[1] == pytest.approx(371.4, abs=0.01)
    assert s.spur_dbc[1] == pytest.approx(20 * math.log10(0.001), abs=1e-3)
    t = measurements.tone_metrics(x, 1024.0)
    assert (s.carrier_power, s.carrier_frequency) == (t.signal_power, t.fundamental_frequency)


@pytest.mark.parametrize("num_spurs", [0, -1, 1.0, True])
def test_sfdr_needs_a_positive_whole_spur_count(num_spurs: object) -> None:
    with pytest.raises(ValueError):
        measurements.sfdr(np.cos(np.arange(32) * 1.2), 32.0, num_spurs=num_spurs)  # type: ignore[arg-type]
