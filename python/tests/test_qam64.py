"""64-QAM map, demap and theory (conventions: Bits and symbols, EVM and BER; ADR 0052)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from signalforge import (
    qam64_ber_theory,
    qam64_demap_hard,
    qam64_demap_llr,
    qam64_map,
    qam64_ser_theory,
)

ALL = ((np.arange(64)[:, None] >> np.arange(5, -1, -1)) & 1).astype(np.uint8).reshape(-1)


def test_unit_energy_and_round_trip() -> None:
    z = qam64_map(ALL)
    assert np.mean(np.abs(z) ** 2) == pytest.approx(1.0, abs=1e-15)
    assert np.array_equal(qam64_demap_hard(z), ALL)


def test_gray_neighbours_differ_in_one_bit() -> None:
    z = qam64_map(ALL)
    labels = ALL.reshape(64, 6)
    d = 2 / math.sqrt(42)
    for a in range(64):
        for b in range(64):
            if abs(abs(z[a] - z[b]) - d) < 1e-12:
                assert np.sum(labels[a] != labels[b]) == 1


def test_llr_sign_is_the_hard_decision() -> None:
    rng = np.random.default_rng(4)
    y = 1.3 * (rng.standard_normal(500) + 1j * rng.standard_normal(500))
    llr = qam64_demap_llr(y, 0.1)
    assert np.array_equal((llr < 0).astype(np.uint8), qam64_demap_hard(y))


def test_ber_and_ser_match_monte_carlo() -> None:
    rng = np.random.default_rng(7)
    eb = 12.0
    n = 100_000
    bits = rng.integers(0, 2, 6 * n).astype(np.uint8)
    z = qam64_map(bits)
    sigma = math.sqrt(10 ** (-(eb + 10 * math.log10(6)) / 10) / 2)
    y = z + sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    got = qam64_demap_hard(y)
    ber = np.mean(got != bits)
    ser = np.mean(np.any(got.reshape(n, 6) != bits.reshape(n, 6), axis=1))
    assert ber == pytest.approx(qam64_ber_theory(eb), rel=0.05)
    assert ser == pytest.approx(qam64_ser_theory(eb), rel=0.05)


def test_theory_limits() -> None:
    assert qam64_ber_theory(-math.inf) == 0.5
    assert qam64_ser_theory(-math.inf) == 63 / 64
    assert qam64_ber_theory(math.inf) == 0.0
    with pytest.raises(ValueError):
        qam64_ber_theory(math.nan)


@pytest.mark.parametrize("bad", [[0, 1, 1], [0, 1, 1, 0, 2, 0], [[0, 1, 1, 0, 1, 0]]])
def test_map_rejects(bad: object) -> None:
    with pytest.raises(ValueError):
        qam64_map(bad)  # type: ignore[arg-type]


def test_demap_rejects_nan() -> None:
    with pytest.raises(ValueError):
        qam64_demap_hard([1, complex(math.nan, 0)])
