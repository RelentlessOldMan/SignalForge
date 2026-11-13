"""Continuous-phase M-FSK, noncoherent detection and theory (conventions: Bits and symbols, FSK;
EVM and BER; ADR 0054)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from signalforge import (
    awgn,
    fsk_ber_theory,
    fsk_demod_noncoherent,
    fsk_modulate,
    fsk_ser_theory,
)

ORDERS = [(2, 1, 4), (4, 2, 8), (8, 3, 16), (16, 4, 32)]


@pytest.mark.parametrize(("order", "k", "sps"), ORDERS)
def test_constant_envelope_and_continuous_phase(order: int, k: int, sps: int) -> None:
    bits = np.random.default_rng(order).integers(0, 2, 60 * k)
    x = fsk_modulate(bits, order, sps, 1.0)
    assert x.size == 60 * sps
    assert np.allclose(np.abs(x), 1.0, atol=1e-15)
    labels = bits.reshape(-1, k) @ (1 << np.arange(k - 1, -1, -1))
    steps = np.angle(x[1:] * np.conj(x[:-1]))
    want = np.repeat(np.pi * (2 * labels - (order - 1)) / sps, sps)[:-1]
    # with h = 1 the step is pi*a/sps, at most pi*(M-1)/sps < pi, so angle() does not wrap
    assert np.allclose(steps, want, atol=1e-9)


@pytest.mark.parametrize(("order", "k", "sps"), ORDERS)
def test_tone_frequency(order: int, k: int, sps: int) -> None:
    for m in range(order):
        bits = np.array([(m >> (k - 1 - i)) & 1 for i in range(k)] * 4)
        x = fsk_modulate(bits, order, sps, 1.0)
        f = np.angle(np.sum(x[1:] * np.conj(x[:-1]))) / (2 * np.pi) * sps  # cycles per symbol
        assert f == pytest.approx((2 * m - (order - 1)) / 2, abs=1e-12)


@pytest.mark.parametrize(("order", "k", "sps"), ORDERS)
def test_noiseless_round_trip_with_phase_and_gain(order: int, k: int, sps: int) -> None:
    bits = np.random.default_rng(7).integers(0, 2, 200 * k)
    x = fsk_modulate(bits, order, sps, 1.0) * 0.3 * np.exp(1.1j)
    assert np.array_equal(fsk_demod_noncoherent(x, order, sps, 1.0), bits)


# About 500 symbol errors each, so 15 % is more than 3 standard deviations.
@pytest.mark.parametrize(
    ("order", "db", "symbols"), [(2, 10.0, 150000), (4, 8.0, 200000), (8, 6.0, 70000)]
)
def test_monte_carlo_matches_theory(order: int, db: float, symbols: int) -> None:
    k = int(math.log2(order))
    sps = 2 * order
    bits = np.random.default_rng(order + 100).integers(0, 2, symbols * k)
    x = fsk_modulate(bits, order, sps, 1.0)
    y = awgn(x, db + 10 * math.log10(k), sps, seed=order, signal_power=1.0)
    got = fsk_demod_noncoherent(y, order, sps, 1.0)
    ber = np.mean(got != bits)
    ser = np.mean(np.any((got != bits).reshape(-1, k), axis=1))
    assert ber == pytest.approx(fsk_ber_theory(db, order), rel=0.15)
    assert ser == pytest.approx(fsk_ser_theory(db, order), rel=0.15)


def test_theory() -> None:
    assert fsk_ber_theory(10.0) == pytest.approx(0.5 * math.exp(-5), rel=1e-14)
    assert fsk_ser_theory(-math.inf, 16) == pytest.approx(15 / 16, abs=1e-13)
    assert fsk_ber_theory(math.inf, 8) == 0.0
    for order in (4, 8, 16):  # more tones need less Eb/N0 for the same bit error rate
        assert fsk_ber_theory(10.0, order) < fsk_ber_theory(10.0, order // 2)


@pytest.mark.parametrize("order", [1, 3, 32, 2.0, True])
def test_bad_order(order: object) -> None:
    with pytest.raises(ValueError, match="order"):
        fsk_modulate([0, 1], order, 8, 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="order"):
        fsk_demod_noncoherent(np.ones(8), order, 8, 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="order"):
        fsk_ber_theory(4.0, order)  # type: ignore[arg-type]


def test_bad_arguments() -> None:
    with pytest.raises(ValueError, match="samples_per_symbol"):
        fsk_modulate([0], 2, 0, 1.0)
    with pytest.raises(ValueError, match="modulation_index"):
        fsk_modulate([0], 2, 4, -1.0)
    with pytest.raises(ValueError, match="modulation_index"):
        fsk_modulate([0], 2, 4, math.inf)
    with pytest.raises(ValueError, match="multiple"):
        fsk_modulate([0, 1, 1], 4, 4, 1.0)
    with pytest.raises(ValueError, match="multiple"):
        fsk_demod_noncoherent(np.ones(5), 2, 4, 1.0)
    with pytest.raises(ValueError, match="finite"):
        fsk_demod_noncoherent([1, np.inf], 2, 2, 1.0)
    with pytest.raises(ValueError, match="NaN"):
        fsk_ser_theory(math.nan, 4)
