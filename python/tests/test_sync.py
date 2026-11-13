"""Synchronization estimators on a full shaped QPSK link with delay, carrier offset and noise."""

from __future__ import annotations

import math

import numpy as np
import pytest

from signalforge import (
    awgn,
    bit_errors,
    convolve,
    fractional_delay,
    frequency_offset,
    prbs,
    pulse_shape,
    qpsk_ber_theory,
    qpsk_demap_hard,
    qpsk_frequency_offset,
    qpsk_map,
    qpsk_phase_offset,
    rrc_taps,
    timing_offset,
)


def _link(
    nsym: int, delay: int, df: float, phase: float, eb_n0_db: float, seed: int
) -> tuple[np.typing.NDArray[np.uint8], np.typing.NDArray[np.complex128], int]:
    """Shaped QPSK at 4 samples per symbol, Rs = 1000, through delay, carrier offset and AWGN."""
    sps = 4
    bits = prbs(15, 2 * nsym)
    h = rrc_taps(0.35, sps, 10)
    tx = np.concatenate([np.zeros(delay, dtype=complex), pulse_shape(qpsk_map(bits), h, sps)])
    tx = frequency_offset(tx, df, 1000.0 * sps, phase)
    es_n0_db = eb_n0_db + 10 * math.log10(2)
    rx = convolve(awgn(tx, es_n0_db, sps, seed=seed, signal_power=1 / sps), h)
    return bits, np.asarray(rx, dtype=np.complex128), h.size - 1 + delay


def _sample(
    rx: np.typing.NDArray[np.complex128], first: int, nsym: int
) -> np.typing.NDArray[np.complex128]:
    tau = timing_offset(rx, 4)
    assert abs(tau - first % 4) < 0.1
    start = first - first % 4 + round(tau) % 4  # the frame start comes from a preamble in practice
    return rx[start : start + nsym * 4 : 4]


def _derotate(
    sampled: np.typing.NDArray[np.complex128], bits: np.typing.NDArray[np.uint8]
) -> np.typing.NDArray[np.complex128]:
    phi = qpsk_phase_offset(sampled)
    z = frequency_offset(sampled, 0.0, 1.0, -phi)
    # resolve the pi/2 ambiguity with the first 32 known symbols
    re, im = _sum(np.conj(qpsk_map(bits[:64])) * z[:32])
    m = round(math.atan2(im, re) / (math.pi / 2))
    return np.asarray(z * np.exp(-1j * m * math.pi / 2), dtype=np.complex128)


def test_recovers_timing_and_phase_at_theory_ber() -> None:
    nsym, eb_n0_db = 100_000, 6.0
    bits, rx, first = _link(nsym, delay=3, df=0.0, phase=2.0, eb_n0_db=eb_n0_db, seed=5)
    z = _derotate(_sample(rx, first, nsym), bits)
    ber = bit_errors(bits, qpsk_demap_hard(z)).rate
    theory = qpsk_ber_theory(eb_n0_db)  # 2.39e-3: about 480 errors
    assert abs(ber - theory) / theory < 0.15


def test_frequency_estimate_accuracy() -> None:
    # The lag-1 estimator's error is about 0.2 Hz here (Rs = 1000, 100k symbols, Eb/N0 6 dB).
    nsym = 100_000
    _, rx, first = _link(nsym, delay=1, df=20.0, phase=0.0, eb_n0_db=6.0, seed=6)
    assert abs(qpsk_frequency_offset(_sample(rx, first, nsym), 1000.0) - 20.0) < 1.0


def test_short_block_with_every_impairment() -> None:
    nsym = 2000
    bits, rx, first = _link(nsym, delay=2, df=37.0, phase=-1.2, eb_n0_db=20.0, seed=7)
    z = _sample(rx, first, nsym)
    z = frequency_offset(z, -qpsk_frequency_offset(z, 1000.0), 1000.0)
    z = _derotate(z, bits)
    assert bit_errors(bits, qpsk_demap_hard(z)).errors == 0


def _sum(x: np.typing.NDArray[np.complex128]) -> tuple[float, float]:
    s = complex(np.sum(x))
    return s.real, s.imag


def test_timing_needs_two_samples_per_symbol() -> None:
    with pytest.raises(ValueError):
        timing_offset(np.ones(4, dtype=complex), 1)
    with pytest.raises(ValueError):
        timing_offset(np.ones(4, dtype=complex), 2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        timing_offset(np.ones((2, 2), dtype=complex), 2)


def test_estimates_are_in_range() -> None:
    rng = np.random.default_rng(0)
    for _ in range(50):
        z = rng.standard_normal(16) + 1j * rng.standard_normal(16)
        assert 0 <= timing_offset(z, 4) < 4
        assert -125 < qpsk_frequency_offset(z, 1000.0) <= 125
        assert -math.pi / 4 < qpsk_phase_offset(z) <= math.pi / 4


@pytest.mark.parametrize("delay", [0.3, 1.7, 2.5, 3.9])
def test_fractional_timing_end_to_end(delay: float) -> None:
    """A burst delayed by part of a sample: Oerder-Meyr finds the delay, and undoing its fraction
    with fractional_delay gives the AWGN error rate back."""
    sps, nsym = 4, 50_000
    bits = prbs(15, 2 * nsym)
    h = rrc_taps(0.35, sps, 10)
    tx = np.concatenate([pulse_shape(qpsk_map(bits), h, sps), np.zeros(64)])
    es_n0_db = 4.0 + 10 * math.log10(2)
    rx = convolve(awgn(fractional_delay(tx, delay), es_n0_db, sps, seed=7, signal_power=1 / sps), h)
    first = h.size - 1 + delay
    tau = timing_offset(rx, sps)
    assert abs((tau - first % sps + 2) % sps - 2) < 0.05
    frac = tau % 1
    start = round(first - frac)  # the whole-sample part comes from a preamble in practice
    fixed = fractional_delay(rx, -frac)
    theory = qpsk_ber_theory(4.0)
    ber = bit_errors(bits, qpsk_demap_hard(fixed[start : start + nsym * sps : sps])).rate
    # 100 000 bits, about 1250 errors: 3 sigma is about 8.5 %
    assert ber == pytest.approx(theory, rel=0.1)
    if delay % 1 > 0.45:  # sampled half a sample or more off, it is clearly worse
        late = math.floor(first)
        late_bits = qpsk_demap_hard(rx[late : late + nsym * sps : sps])
        assert bit_errors(bits, late_bits).rate > 1.3 * theory
