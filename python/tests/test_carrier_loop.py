"""Decision-directed QPSK carrier tracking against its definition and the loop model (conventions:
Synchronization, Tracking loops)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf

SPS = 4


def _rotated(
    nsym: int, theta0: float, omega: float
) -> tuple[NDArray[np.complex128], NDArray[np.float64]]:
    k = np.arange(nsym)
    theta = np.asarray(theta0 + omega * k, dtype=np.float64)
    z = sf.qpsk_map(sf.prbs(15, 2 * nsym)) * np.exp(1j * theta)
    return np.asarray(z, dtype=np.complex128), theta


def test_proportional_lag_is_exact() -> None:
    omega, kp = 0.01, 0.1
    z, theta = _rotated(1000, 0.4, omega)
    r = sf.qpsk_carrier_tracking(z, kp, 0.0)
    want = math.asin(omega / (math.sqrt(2) * kp))
    np.testing.assert_allclose((theta - r.phases)[500:], want, rtol=0, atol=1e-9)


def test_integrator_removes_the_lag() -> None:
    omega = 0.01
    kp, ki = sf.pi_loop_gains(0.02, 1 / math.sqrt(2), math.sqrt(2))
    z, theta = _rotated(3000, 0.4, omega)
    r = sf.qpsk_carrier_tracking(z, kp, ki)
    np.testing.assert_allclose((theta - r.phases)[2000:], 0, rtol=0, atol=1e-9)
    np.testing.assert_allclose(np.diff(r.phases)[2000:], omega, rtol=1e-9)


def test_locks_with_a_start_phase_and_reports_it() -> None:
    z, _ = _rotated(50, 0.2, 0.0)
    r = sf.qpsk_carrier_tracking(z, 0.3, 0.0, phase=0.2)
    np.testing.assert_allclose(r.errors, 0, atol=1e-14)
    np.testing.assert_allclose(r.phases, 0.2, atol=1e-14)
    np.testing.assert_allclose(r.symbols, z * np.exp(-0.2j), atol=1e-15)


def test_full_link_after_timing_recovery() -> None:
    nsym, offset = 8000, 1e-4  # carrier offset in cycles per sample
    bits = sf.prbs(15, 2 * nsym)
    h = sf.rrc_taps(0.35, SPS, 10)
    tx = np.concatenate([sf.pulse_shape(sf.qpsk_map(bits), h, SPS), np.zeros(64)])
    first = h.size - 1
    clean = sf.convolve(tx, h)
    late = sf.gardner_timing(clean, SPS, 0.0, 0.0, start=first + 0.1).errors[1:1500].mean()
    early = sf.gardner_timing(clean, SPS, 0.0, 0.0, start=first - 0.1).errors[1:1500].mean()
    tkp, tki = sf.pi_loop_gains(0.005, 1 / math.sqrt(2), float(late - early) / 0.2)
    moved = sf.frequency_offset(sf.fractional_delay(tx, 2.3), offset, 1.0, 0.3)
    es_n0_db = 4.0 + 10 * math.log10(2)
    rx = sf.convolve(sf.awgn(moved, es_n0_db, SPS, seed=4, signal_power=1 / SPS), h)
    timed = sf.gardner_timing(rx, SPS, tkp, tki, start=first + 2)
    ckp, cki = sf.pi_loop_gains(0.01, 1 / math.sqrt(2), math.sqrt(2))
    r = sf.qpsk_carrier_tracking(timed.symbols[:nsym], ckp, cki)
    # the integrator settles on the offset per symbol
    slope = np.polyfit(np.arange(1000, nsym), r.phases[1000:], 1)[0]
    assert slope == pytest.approx(2 * math.pi * offset * SPS, rel=0.05)
    ber = sf.bit_errors(bits[2000:], sf.qpsk_demap_hard(r.symbols[1000:])).rate
    # 14 000 bits, about 175 errors: 3 sigma is about 23 %; both loops' jitter costs a little
    assert ber == pytest.approx(sf.qpsk_ber_theory(4.0), rel=0.3)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.qpsk_carrier_tracking([[1.0]], 0.1, 0.0),
        lambda: sf.qpsk_carrier_tracking([1.0], -0.1, 0.0),
        lambda: sf.qpsk_carrier_tracking([1.0], 0.1, math.inf),
        lambda: sf.qpsk_carrier_tracking([1.0], 0.1, 0.0, phase=math.nan),
        lambda: sf.qpsk_carrier_tracking([1.0], True, 0.0),
        lambda: sf.qpsk_carrier_tracking([complex(1, math.inf)], 0.1, 0.0),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
