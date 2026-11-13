"""Soft demapping: the sign is the hard decision, QPSK's closed form, the bound against the exact
log-sum LLR, and scaling with the noise variance (conventions: Bits and symbols, Soft demapping)."""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import pytest

import signalforge as sf

Demap = Callable[[np.ndarray], np.ndarray]
SoftDemap = Callable[[np.ndarray, float], np.ndarray]
CASES = [
    (2, sf.qpsk_map, sf.qpsk_demap_hard, sf.qpsk_demap_llr),
    (3, sf.psk8_map, sf.psk8_demap_hard, sf.psk8_demap_llr),
    (4, sf.qam16_map, sf.qam16_demap_hard, sf.qam16_demap_llr),
]


def _noisy(k: int, mapper: Demap, n0: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    bits = sf.prbs(11, k * 2047)
    return bits, sf.awgn(mapper(bits), 10 * math.log10(1 / n0), seed=seed, signal_power=1.0)


@pytest.mark.parametrize(("k", "mapper", "hard", "soft"), CASES)
def test_sign_is_the_hard_decision(k: int, mapper: Demap, hard: Demap, soft: SoftDemap) -> None:
    _, y = _noisy(k, mapper, 0.2, 1)
    llr = soft(y, 0.2)
    assert llr.shape == (k * y.size,)
    decided = hard(y)
    away = np.abs(llr) > 1e-9  # off the decision boundaries
    np.testing.assert_array_equal((llr < 0)[away], decided[away] == 1)


@pytest.mark.parametrize(("k", "mapper", "hard", "soft"), CASES)
def test_within_the_bound_of_the_exact_llr(
    k: int, mapper: Demap, hard: Demap, soft: SoftDemap
) -> None:
    n0 = 0.3
    points = mapper(((np.arange(1 << k)[:, None] >> np.arange(k - 1, -1, -1)) & 1).reshape(-1))
    _, y = _noisy(k, mapper, n0, 2)
    metric = -(np.abs(y[:, None] - points[None, :]) ** 2) / n0
    labels = np.arange(1 << k)
    exact = np.empty((y.size, k))
    for i in range(k):
        one = ((labels >> (k - 1 - i)) & 1) == 1
        exact[:, i] = np.logaddexp.reduce(metric[:, ~one], axis=1) - np.logaddexp.reduce(
            metric[:, one], axis=1
        )
    diff = np.abs(soft(y, n0) - exact.reshape(-1))
    assert diff.max() <= math.log((1 << k) / 2) + 1e-9
    if k == 2:
        assert diff.max() < 1e-9  # max-log is exact for QPSK


def test_qpsk_closed_form_and_scaling() -> None:
    rng = np.random.default_rng(4)
    y = rng.standard_normal(100) + 1j * rng.standard_normal(100)
    llr = sf.qpsk_demap_llr(y, 0.7)
    np.testing.assert_allclose(llr[0::2], 2 * math.sqrt(2) * y.real / 0.7, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(llr[1::2], 2 * math.sqrt(2) * y.imag / 0.7, rtol=1e-12, atol=1e-12)
    for soft in (sf.psk8_demap_llr, sf.qam16_demap_llr):
        np.testing.assert_allclose(soft(y, 2.0), soft(y, 1.0) / 2, rtol=1e-15)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.qpsk_demap_llr([[1j]], 1.0),
        lambda: sf.psk8_demap_llr([1j], -1.0),
        lambda: sf.qam16_demap_llr([1j], True),
        lambda: sf.qam16_demap_llr([complex(math.inf, 0)], 1.0),
    ],
)
def test_bad_arguments_raise(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError):
        call()
