"""Gardner timing recovery against its definition and the linear loop model (conventions:
Synchronization, Tracking loops)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf

SPS = 4


def _burst(nsym: int) -> tuple[NDArray[np.uint8], NDArray[np.complex128], int]:
    """Matched-filter output of shaped QPSK, noise-free, and where its first symbol peaks."""
    bits = sf.prbs(15, 2 * nsym)
    h = sf.rrc_taps(0.35, SPS, 10)
    tx = np.concatenate([sf.pulse_shape(sf.qpsk_map(bits), h, SPS), np.zeros(64)])
    return bits, np.asarray(sf.convolve(tx, h), dtype=np.complex128), h.size - 1


def _raised_cosine_burst(nsym: int, drift: float) -> tuple[NDArray[np.complex128], float]:
    """QPSK through a raised-cosine pulse (roll-off 0.5) written out analytically, symbol k
    peaking at first + k*SPS*(1 + drift): a transmitter whose clock runs slow by `drift`."""
    rng = np.random.default_rng(2)
    a = (rng.choice([-1.0, 1.0], nsym) + 1j * rng.choice([-1.0, 1.0], nsym)) / math.sqrt(2)
    first = 48.0
    n = np.arange(int(first + nsym * SPS * (1 + drift)) + 48)
    y = np.zeros(n.size, dtype=complex)
    for k in range(nsym):
        x = (n - first - k * SPS * (1 + drift)) / SPS
        near = np.abs(x) < 12
        xs = x[near]
        with np.errstate(invalid="ignore", divide="ignore"):
            p = np.sinc(xs) * np.cos(math.pi * 0.5 * xs) / (1 - xs**2)
        p = np.where(np.abs(np.abs(xs) - 1) < 1e-12, math.pi / 4 * np.sinc(1.0), p)
        y[near] += a[k] * p
    return y, first


def _detector_gain(y: NDArray[np.complex128], first: float, nsym: int) -> float:
    """The S-curve's slope at lock, from the open loop a tenth of a sample either side."""
    late = sf.gardner_timing(y, SPS, 0.0, 0.0, start=first + 0.1).errors[1:nsym].mean()
    early = sf.gardner_timing(y, SPS, 0.0, 0.0, start=first - 0.1).errors[1:nsym].mean()
    return float(late - early) / 0.2


def test_open_loop_reads_like_fractional_delay() -> None:
    _, y, _ = _burst(200)
    r = sf.gardner_timing(y, SPS, 0.0, 0.0, start=1.25)
    want = sf.fractional_delay(y, -1.25, half_width=8)[::SPS][: r.symbols.size]
    np.testing.assert_allclose(r.symbols, want, rtol=0, atol=1e-14)
    np.testing.assert_array_equal(r.positions, 1.25 + SPS * np.arange(r.symbols.size))
    assert r.errors[0] == 0


def test_s_curve_is_odd_and_positive_late() -> None:
    _, y, first = _burst(1500)
    for eps in (0.1, 0.3, 0.6):
        late = sf.gardner_timing(y, SPS, 0.0, 0.0, start=first + eps).errors[1:1400].mean()
        early = sf.gardner_timing(y, SPS, 0.0, 0.0, start=first - eps).errors[1:1400].mean()
        assert late > 0 > early
        assert abs(late + early) < 0.05 * late


def test_locks_to_a_fractional_offset_in_noise() -> None:
    nsym = 6000
    bits, y, first = _burst(nsym)
    kp, ki = sf.pi_loop_gains(0.005, 1 / math.sqrt(2), _detector_gain(y, first, 1500))
    es_n0_db = 2.0 + 10 * math.log10(2)
    h = sf.rrc_taps(0.35, SPS, 10)
    tx = np.concatenate([sf.pulse_shape(sf.qpsk_map(bits), h, SPS), np.zeros(64)])
    noisy = sf.awgn(sf.fractional_delay(tx, 2.3), es_n0_db, SPS, seed=6, signal_power=1 / SPS)
    rx = sf.convolve(noisy, h)
    r = sf.gardner_timing(rx, SPS, kp, ki, start=first + 2)  # starts 0.3 samples early
    err = r.positions - (first + 2.3 + SPS * np.arange(r.positions.size))
    assert err[0] == pytest.approx(-0.3, abs=1e-12)
    # noise-free the loop sits within 0.01 samples; in noise it jitters by about 0.15 rms and
    # wanders slowly (about 56 independent stretches here), so the mean has a spread of about 0.02
    assert abs(err[400:nsym].mean()) < 0.06
    assert np.sqrt(np.mean(err[400:nsym] ** 2)) < 0.25
    got = sf.qpsk_demap_hard(r.symbols[400:nsym])
    ber = sf.bit_errors(bits[800 : 2 * nsym], got).rate
    # 11 200 bits, about 420 errors: 3 sigma is about 15 %; the loop's jitter costs a little
    assert ber == pytest.approx(sf.qpsk_ber_theory(2.0), rel=0.2)


def test_drift_lag_follows_the_linear_model() -> None:
    nsym, drift = 1500, 1e-3
    y0, first = _raised_cosine_burst(nsym, 0.0)
    kd = _detector_gain(y0, first, nsym - 10)
    y, first = _raised_cosine_burst(nsym, drift)
    kp, ki = sf.pi_loop_gains(0.02, 1 / math.sqrt(2), kd)
    truth = first + SPS * (1 + drift) * np.arange(nsym)
    proportional = sf.gardner_timing(y, SPS, kp, 0.0, start=first)
    lag = (proportional.positions[: nsym - 10] - truth[: nsym - 10])[300:].mean()
    assert lag == pytest.approx(-SPS * drift / (kp * kd), rel=0.25)
    tracked = sf.gardner_timing(y, SPS, kp, ki, start=first)
    assert abs((tracked.positions[: nsym - 10] - truth[: nsym - 10])[300:].mean()) < 0.01


def test_pi_loop_gains_by_hand() -> None:
    kp, ki = sf.pi_loop_gains(0.01, 1 / math.sqrt(2), 1.0)
    theta = 0.01 / (1 / math.sqrt(2) + math.sqrt(2) / 4)
    d = 1 + math.sqrt(2) * theta + theta**2
    assert kp == pytest.approx(2 * math.sqrt(2) * theta / d, rel=1e-14)
    assert ki == pytest.approx(4 * theta**2 / d, rel=1e-14)
    assert sf.pi_loop_gains(0.01, 1 / math.sqrt(2), 2.0)[0] == pytest.approx(kp / 2, rel=1e-15)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.gardner_timing([[1.0]], 2, 0.1, 0.0),
        lambda: sf.gardner_timing([1.0], 2.0, 0.1, 0.0),  # type: ignore[arg-type]
        lambda: sf.gardner_timing([1.0], 2, math.inf, 0.0),
        lambda: sf.gardner_timing([1.0], 2, 0.1, -1e-3),
        lambda: sf.gardner_timing([1.0], 2, 0.1, 0.0, start=math.nan),
        lambda: sf.gardner_timing([math.nan], 2, 0.1, 0.0),
        lambda: sf.pi_loop_gains(0.01, math.inf, 1.0),
        lambda: sf.pi_loop_gains(0.01, 1.0, 0.0),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
