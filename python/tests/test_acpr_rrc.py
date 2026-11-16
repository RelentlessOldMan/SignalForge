"""ACPR through a root-raised-cosine channel filter (conventions: Spectra, ACPR; ADR 0111)."""

import math

import numpy as np
import pytest

from signalforge import acpr_rrc, pulse_shape, qpsk_map, rrc_taps, welch_psd

F = np.arange(-256, 256) / 8.0  # 1/8 Hz bins from -32 to 32 Hz


@pytest.mark.parametrize("alpha", [0.1, 0.22, 0.35, 0.5, 1.0])
@pytest.mark.parametrize("center", [0.0, 0.03, -1.3, 2.0625])
def test_flat_psd_reads_level_times_symbol_rate_wherever_the_bins_fall(
    alpha: float, center: float
) -> None:
    # R/delta = 24 is whole, so the raised cosine's bin sum is exactly R (Poisson summation)
    r = acpr_rrc(F, np.full(F.size, 0.5), center, 3.0, alpha, [5.0, 9.5])
    assert r.main_power == pytest.approx(1.5, rel=1e-12)
    np.testing.assert_allclose(r.lower_power, 1.5, rtol=1e-12)
    np.testing.assert_allclose(r.upper_power, 1.5, rtol=1e-12)
    np.testing.assert_allclose(r.lower_dbc, 0.0, atol=1e-11)


@pytest.mark.parametrize("alpha", [0.25, 0.6, 1.0])
def test_a_single_line_reads_the_squared_cosine_taper(alpha: float) -> None:
    # G = cos^2(pi (|x| - (1 - a)R/2) / (2 a R)) on the taper: the same curve written differently
    rs = 4.0
    flat, edge = (1 - alpha) * rs / 2, (1 + alpha) * rs / 2
    for k in range(F.size):
        x = abs(float(F[k]) - 10.0)
        if x > edge + 1:
            continue
        psd = np.zeros(F.size)
        psd[256] = 1.0  # main channel at 0 Hz
        psd[k] += 2.0
        r = acpr_rrc(F, psd, 0.0, rs, alpha, [10.0])
        g = 1.0 if x <= flat else math.cos(math.pi * (x - flat) / (2 * alpha * rs)) ** 2
        if x >= edge:
            g = 0.0
        assert r.upper_power[0] == pytest.approx(2.0 * 0.125 * g, abs=1e-15)
        assert r.main_power == pytest.approx(0.125, rel=1e-12)


def test_rrc_qpsk_keeps_one_minus_alpha_over_four_and_leaks_nothing_next_door() -> None:
    # A transmit RRC gives a raised-cosine PSD; through the receive weight it integrates to
    # R (1 - alpha/4) of the total R
    sps, alpha = 8, 0.35
    rng = np.random.default_rng(11)
    x = pulse_shape(qpsk_map(rng.integers(0, 2, 2 * 20000)), rrc_taps(alpha, sps, 32), sps)
    s = welch_psd(x, float(sps), nperseg=1024, window="blackman_harris")
    total = float(np.sum(s.psd)) * (s.frequencies[1] - s.frequencies[0])
    r = acpr_rrc(s.frequencies, s.psd, 0.0, 1.0, alpha, [1.0 + alpha, 2.0])
    assert r.main_power / total == pytest.approx(1 - alpha / 4, rel=0.01)
    assert np.all(r.lower_dbc < -40) and np.all(r.upper_dbc < -40)


def test_white_noise_reads_the_same_in_every_channel() -> None:
    rng = np.random.default_rng(5)
    n = (rng.standard_normal(1 << 18) + 1j * rng.standard_normal(1 << 18)) / math.sqrt(2)
    s = welch_psd(n, 8.0, nperseg=256)
    r = acpr_rrc(s.frequencies, s.psd, 0.0, 1.0, 0.22, [1.0, 2.0])
    assert r.main_power == pytest.approx(1 / 8, rel=0.03)  # R N0, N0 = 1/fs
    np.testing.assert_allclose(r.lower_dbc, 0.0, atol=0.3)
    np.testing.assert_allclose(r.upper_dbc, 0.0, atol=0.3)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"alpha": 0.0}, "alpha"),
        ({"alpha": -0.1}, "alpha"),
        ({"symbol_rate": -1.0}, "symbol_rate"),
        ({"offsets": [40.0]}, "leaves the spectrum"),
        ({"center": 31.0}, "leaves the spectrum"),
    ],
)
def test_bad_arguments(kwargs: dict[str, object], match: str) -> None:
    args: dict[str, object] = {"center": 0.0, "symbol_rate": 3.0, "alpha": 0.5, "offsets": [5.0]}
    args.update(kwargs)
    with pytest.raises(ValueError, match=match):
        acpr_rrc(F, np.ones(F.size), **args)  # type: ignore[arg-type]
