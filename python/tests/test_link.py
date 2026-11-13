"""Pulse shaping, channel and link metrics: properties that the vectors cannot check."""

from __future__ import annotations

import math

import numpy as np
import pytest

from signalforge import (
    awgn,
    bit_errors,
    convolve,
    evm,
    frequency_offset,
    prbs,
    pulse_shape,
    qpsk_ber_theory,
    qpsk_demap_hard,
    qpsk_map,
    rrc_taps,
)


@pytest.mark.parametrize(("beta", "sps", "span"), [(0.35, 4, 8), (0.25, 4, 4), (1.0, 2, 6)])
def test_rrc_unit_energy_symmetric(beta: float, sps: int, span: int) -> None:
    h = rrc_taps(beta, sps, span)
    assert h.size == span * sps + 1
    assert math.isclose(float(np.sum(h * h)), 1.0, rel_tol=1e-14)
    np.testing.assert_allclose(h, h[::-1], atol=1e-15)


def test_matched_filter_is_nearly_nyquist() -> None:
    # RRC * RRC is a raised cosine: zero crossings at nonzero symbol instants (up to truncation).
    sps, span = 8, 16
    h = rrc_taps(0.35, sps, span)
    rc = convolve(h, h)
    center = h.size - 1
    assert math.isclose(float(rc[center]), 1.0, rel_tol=1e-14)
    others = [abs(float(rc[center + k * sps])) for k in range(-span, span + 1) if k]
    assert max(others) < 2e-3


def test_shaped_qpsk_round_trip() -> None:
    sps, span = 4, 10
    bits = prbs(9, 400)
    symbols = qpsk_map(bits)
    h = rrc_taps(0.35, sps, span)
    rx = convolve(pulse_shape(symbols, h, sps), h)
    n = h.size
    sampled = rx[n - 1 : n - 1 + symbols.size * sps : sps]
    assert evm(sampled, symbols).rms < 0.02
    np.testing.assert_array_equal(qpsk_demap_hard(sampled), bits)


def test_shaped_power_is_es_over_sps() -> None:
    sps = 4
    symbols = qpsk_map(prbs(11, 4000))
    tx = pulse_shape(symbols, rrc_taps(0.35, sps, 10), sps)
    # total energy = symbols * Es (unit energy taps, uncorrelated symbols)
    energy = float(np.sum(np.abs(tx) ** 2))
    assert math.isclose(energy / symbols.size, 1.0, rel_tol=0.03)


def test_awgn_variance_and_seed() -> None:
    x = np.ones(200_000, dtype=complex)
    y = awgn(x, 10.0, seed=1)
    noise = y - x
    assert math.isclose(float(np.mean(np.abs(noise) ** 2)), 0.1, rel_tol=0.01)
    assert math.isclose(float(np.var(noise.real)), float(np.var(noise.imag)), rel_tol=0.02)
    assert abs(float(np.mean(noise.real * noise.imag))) < 1e-3
    np.testing.assert_array_equal(awgn(x, 10.0, seed=1), y)
    assert not np.array_equal(awgn(x, 10.0, seed=2), y)


def test_awgn_signal_power_and_sps() -> None:
    x = np.full(100_000, 0.5 + 0j)  # measured power 0.25
    noise = awgn(x, 0.0, 4, seed=3, signal_power=2.0) - x
    assert math.isclose(float(np.mean(np.abs(noise) ** 2)), 8.0, rel_tol=0.02)
    noise = awgn(x, 3.0, 2, seed=rng_seed()) - x
    assert math.isclose(float(np.mean(np.abs(noise) ** 2)), 0.5 / 10**0.3, rel_tol=0.02)


def rng_seed() -> np.random.Generator:
    return np.random.default_rng(7)


@pytest.mark.parametrize(
    ("samples", "kwargs"),
    [
        (np.ones(4), {}),  # real samples
        (np.ones(0, dtype=complex), {}),
        (np.array([1 + 0j, np.nan]), {}),
        (np.ones(4, dtype=complex), {"signal_power": 0.0}),
        (np.ones(4, dtype=complex), {"signal_power": math.inf}),
        (np.ones(4, dtype=complex), {"samples_per_symbol": 0}),
        (np.ones(4, dtype=complex), {"samples_per_symbol": 2.0}),
        (np.ones(4, dtype=complex), {"es_n0_db": math.nan}),
        (np.zeros(4, dtype=complex), {}),  # measured power zero
    ],
)
def test_awgn_rejects(samples: np.ndarray, kwargs: dict[str, object]) -> None:
    args: dict[str, object] = {"es_n0_db": 10.0, "seed": 0, **kwargs}
    with pytest.raises(ValueError):
        awgn(samples, **args)  # type: ignore[arg-type]


def test_frequency_offset_moves_spectrum() -> None:
    n, fs = 64, 64.0
    y = frequency_offset(np.ones(n, dtype=complex), 5.0, fs)
    assert int(np.argmax(np.abs(np.fft.fft(y)))) == 5
    y = frequency_offset(np.ones(n, dtype=complex), -3.0, fs)
    assert int(np.argmax(np.abs(np.fft.fft(y)))) == n - 3


def test_qpsk_link_ber_matches_theory() -> None:
    sps, span = 4, 10
    bits = prbs(15, 200_000)
    symbols = qpsk_map(bits)
    h = rrc_taps(0.35, sps, span)
    eb_n0_db = 4.0
    es_n0_db = eb_n0_db + 10 * math.log10(2)
    tx = pulse_shape(symbols, h, sps)
    rx = convolve(awgn(tx, es_n0_db, sps, seed=11, signal_power=1 / sps), h)
    sampled = rx[h.size - 1 : h.size - 1 + symbols.size * sps : sps]
    ber = bit_errors(bits, qpsk_demap_hard(sampled)).rate
    theory = qpsk_ber_theory(eb_n0_db)  # 0.0125
    # ~2500 errors expected: 3 sigma is about 6 %; the truncated filter adds a little ISI
    assert abs(ber - theory) / theory < 0.08


def test_qpsk_ber_theory_limits() -> None:
    assert qpsk_ber_theory(-math.inf) == 0.5
    assert qpsk_ber_theory(math.inf) == 0.0
    assert math.isclose(qpsk_ber_theory(9.6), 1.0e-5, rel_tol=0.05)  # the textbook 1e-5 point


def test_evm_peak_and_db() -> None:
    ref = qpsk_map(prbs(7, 20))
    meas = ref.copy()
    meas[3] += 0.3j
    meas[7] += 0.1
    r = evm(meas, ref)
    assert r.peak_index == 3
    assert math.isclose(r.peak, 0.3)
    assert math.isclose(r.rms, math.sqrt(0.1 / 10))
    assert math.isclose(r.rms_db, 20 * math.log10(r.rms))
    with pytest.raises(ValueError):
        evm(np.array([np.nan + 0j]), np.array([1 + 0j]))


def test_counts_must_be_integers() -> None:
    from signalforge import upsample

    with pytest.raises(ValueError):
        upsample([1.0], 2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        rrc_taps(0.35, 4.0, 4)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        awgn(np.ones(2, dtype=complex), 0.0, seed=1.5)  # type: ignore[arg-type]
    np.testing.assert_array_equal(upsample([1.0], np.int64(2)), [1.0, 0.0])  # type: ignore[arg-type]
