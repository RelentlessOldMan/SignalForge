"""power_frequency_offset on 16-QAM and 8-PSK, where the lag-1 fourth-power estimator fails."""

from __future__ import annotations

import math

import numpy as np
import pytest

from signalforge import (
    frequency_offset,
    power_frequency_offset,
    psk8_map,
    qam16_map,
    qpsk_frequency_offset,
)

RS = 1000.0


def _noisy(
    a: np.typing.NDArray[np.complex128], es_n0_db: float | None, rng: np.random.Generator
) -> np.typing.NDArray[np.complex128]:
    if es_n0_db is None:
        return a
    sigma = math.sqrt(10 ** (-es_n0_db / 10) / 2)
    n = a.size
    return np.asarray(
        a + sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n)), dtype=np.complex128
    )


def _errors(
    mapper: object, bits_per_symbol: int, n: int, es_n0_db: float | None, power: int
) -> tuple[np.typing.NDArray[np.float64], np.typing.NDArray[np.float64]]:
    """Errors of the new estimator and of the lag-1 one over 20 random offsets and phases."""
    rng = np.random.default_rng(5)
    new, old = [], []
    limit = RS / (2 * power)
    for _ in range(20):
        a = mapper(rng.integers(0, 2, bits_per_symbol * n))  # type: ignore[operator]
        f = rng.uniform(-0.8, 0.8) * limit
        z = _noisy(frequency_offset(a, f, RS, rng.uniform(-3, 3)), es_n0_db, rng)
        new.append(power_frequency_offset(z, RS, power) - f)
        old.append(qpsk_frequency_offset(z, RS) - f)
    return np.abs(new), np.abs(old)


def test_noiseless_qam16_where_lag1_fails() -> None:
    new, old = _errors(qam16_map, 4, 400, None, 4)
    assert new.max() < 0.1
    assert math.sqrt(np.mean(old**2)) > 3  # the reason for this estimator (ADR 0049)


def test_qam16_through_noise() -> None:
    new, _ = _errors(qam16_map, 4, 2000, 14.0, 4)  # Eb/N0 8 dB
    assert new.max() < 0.05


def test_psk8_eighth_power() -> None:
    new, _ = _errors(psk8_map, 3, 1000, 16.0, 8)
    assert new.max() < 0.1


def test_in_range() -> None:
    rng = np.random.default_rng(2)
    for p in (1, 2, 4, 8, 16):
        for _ in range(10):
            z = rng.standard_normal(37) + 1j * rng.standard_normal(37)
            f = power_frequency_offset(z, RS, p)
            assert -RS / (2 * p) < f <= RS / (2 * p)


def test_does_not_change_the_input() -> None:
    z = np.exp(2j * np.pi * 0.01 * np.arange(16))
    before = z.copy()
    power_frequency_offset(z, RS, 4)
    assert np.array_equal(z, before)


@pytest.mark.parametrize(
    ("symbols", "rate", "power"),
    [
        ([1, 1j], RS, 4.0),
        ([1, 1j], RS, True),
        ([1, 1j], RS, 0),
        ([1, 1j], RS, 17),
        ([1, 1j], math.inf, 4),
        ([1, math.nan], RS, 4),
        ([[1, 1j], [1, 1j]], RS, 4),
        ([1], RS, 4),
    ],
)
def test_rejects(symbols: object, rate: float, power: object) -> None:
    with pytest.raises(ValueError):
        power_frequency_offset(symbols, rate, power)  # type: ignore[arg-type]
