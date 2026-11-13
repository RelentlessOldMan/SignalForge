"""16-QAM and 8-PSK error-rate theory: limits, the textbook approximations at high SNR, and
Monte-Carlo runs through the mappers, AWGN and the hard demappers (conventions: EVM and BER)."""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable

import numpy as np
import pytest

import signalforge as sf

THEORIES = [sf.qam16_ber_theory, sf.qam16_ser_theory, sf.psk8_ber_theory, sf.psk8_ser_theory]


@pytest.mark.parametrize(
    ("theory", "guess"),
    list(zip(THEORIES, [0.5, 15 / 16, 0.5, 7 / 8], strict=True)),
)
def test_limits(theory: Callable[[float], float], guess: float) -> None:
    assert theory(-math.inf) == pytest.approx(guess, abs=1e-15)
    assert theory(math.inf) == 0.0
    assert theory(5000.0) == 0.0
    values = [theory(db) for db in np.arange(-10.0, 20.0, 0.5)]
    assert all(a > b for a, b in itertools.pairwise(values))
    with pytest.raises(ValueError):
        theory(math.nan)


def _q(x: float) -> float:
    return 0.5 * math.erfc(x / math.sqrt(2))


def test_high_snr_approximations() -> None:
    for db in (14.0, 18.0):
        es_n0 = 3 * 10 ** (db / 10)
        approx = 2 * _q(math.sqrt(2 * es_n0) * math.sin(math.pi / 8))
        assert sf.psk8_ser_theory(db) == pytest.approx(approx, rel=1e-3)
        assert sf.psk8_ber_theory(db) == pytest.approx(sf.psk8_ser_theory(db) / 3, rel=1e-3)
        assert sf.qam16_ber_theory(db) == pytest.approx(sf.qam16_ser_theory(db) / 4, rel=1e-3)


@pytest.mark.parametrize(
    ("k", "mapper", "demapper", "ber", "ser", "symbols"),
    [
        (4, sf.qam16_map, sf.qam16_demap_hard, sf.qam16_ber_theory, sf.qam16_ser_theory, 150_000),
        (3, sf.psk8_map, sf.psk8_demap_hard, sf.psk8_ber_theory, sf.psk8_ser_theory, 200_000),
    ],
)
def test_monte_carlo(
    k: int,
    mapper: Callable[[np.ndarray], np.ndarray],
    demapper: Callable[[np.ndarray], np.ndarray],
    ber: Callable[[float], float],
    ser: Callable[[float], float],
    symbols: int,
) -> None:
    eb_n0_db = 8.0
    bits = sf.prbs(23, k * symbols)
    rx = sf.awgn(mapper(bits), eb_n0_db + 10 * math.log10(k), seed=12, signal_power=1.0)
    wrong = np.asarray(demapper(rx)) != bits
    # about 4000 to 5500 errors of each kind: 3 sigma is under 5 %
    assert wrong.mean() == pytest.approx(ber(eb_n0_db), rel=0.06)
    assert wrong.reshape(-1, k).any(axis=1).mean() == pytest.approx(ser(eb_n0_db), rel=0.06)
