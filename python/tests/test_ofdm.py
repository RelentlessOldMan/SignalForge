"""OFDM modulate and demodulate (conventions: Bits and symbols, OFDM; ADR 0060)."""

from __future__ import annotations

import numpy as np
import pytest

from signalforge import multipath, ofdm_demodulate, ofdm_modulate, qpsk_map

RNG = np.random.default_rng(60)
USED = [k for k in range(-26, 27) if k != 0]  # a 64-point plan with DC and guard bands empty


def _qpsk(n: int) -> np.ndarray:
    return qpsk_map(RNG.integers(0, 2, 2 * n))


def test_round_trip_and_length() -> None:
    s = _qpsk(10 * len(USED))
    x = ofdm_modulate(s, 64, 16, USED)
    assert x.size == 10 * 80
    assert np.allclose(ofdm_demodulate(x, 64, 16, USED), s, atol=1e-12)


def test_energy_is_kept() -> None:
    s = _qpsk(4 * len(USED))
    x = ofdm_modulate(s, 64, 0, USED)
    assert np.isclose(np.sum(np.abs(x) ** 2), np.sum(np.abs(s) ** 2), rtol=1e-12)
    # mean sample power is the symbol energy times U/N
    assert np.isclose(np.mean(np.abs(x) ** 2), len(USED) / 64, rtol=1e-12)


def test_prefix_is_the_block_tail() -> None:
    x = ofdm_modulate(_qpsk(3 * len(USED)), 64, 16, USED).reshape(3, 80)
    assert np.array_equal(x[:, :16], x[:, 64:])


def test_multipath_within_the_prefix_is_one_gain_per_subcarrier() -> None:
    delays, gains = [0, 3, 9], np.array([1.0, 0.4 - 0.3j, 0.15j])
    s = _qpsk(6 * len(USED))
    y = multipath(ofdm_modulate(s, 64, 16, USED), delays, gains)
    k = np.array(USED)
    h = np.array([np.sum(gains * np.exp(-2j * np.pi * kk * np.array(delays) / 64)) for kk in k])
    r = ofdm_demodulate(y, 64, 16, USED).reshape(6, -1)
    # the first block sees zeros before it, which the prefix also absorbs
    assert np.allclose(r, s.reshape(6, -1) * h, atol=1e-12)


def test_default_subcarriers_are_all_ascending() -> None:
    s = _qpsk(8)
    assert np.allclose(ofdm_modulate(s, 8, 2), ofdm_modulate(s, 8, 2, list(range(-4, 4))))


@pytest.mark.parametrize(
    "subcarriers", [[0.5, 1.0], [True, False], np.zeros((1, 2), dtype=int), ["0", "1"]]
)
def test_rejects_subcarriers_that_are_not_integers(subcarriers: object) -> None:
    with pytest.raises(ValueError):
        ofdm_modulate([1, 1], 4, 0, subcarriers)  # type: ignore[arg-type]


@pytest.mark.parametrize("nfft", [2.0, True, -1])
def test_rejects_bad_nfft(nfft: object) -> None:
    with pytest.raises(ValueError):
        ofdm_modulate([1, 1], nfft, 0)  # type: ignore[arg-type]


def test_rejects_non_numeric_symbols() -> None:
    with pytest.raises(ValueError):
        ofdm_modulate(["a", "b"], 2, 0)
    with pytest.raises(ValueError):
        ofdm_demodulate([[1, 2]], 2, 0)
