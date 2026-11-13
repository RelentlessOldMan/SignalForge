"""Symbol mapping. Definitions in docs/conventions.md."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

_INV_SQRT2 = 1.0 / np.sqrt(2.0)
_INV_SQRT10 = 1.0 / math.sqrt(10.0)
_QAM16_THRESHOLD = 2.0 / math.sqrt(10.0)


def _bits(bits: ArrayLike) -> NDArray[np.uint8]:
    b = np.asarray(bits)
    if b.ndim != 1:
        raise ValueError("bits must be one-dimensional")
    if b.size and not np.all((b == 0) | (b == 1)):
        raise ValueError("bits must be 0 or 1")
    return b.astype(np.uint8)


def qpsk_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded QPSK: bit pair ``(b0, b1)`` to ``((1-2*b0) + j*(1-2*b1)) / sqrt(2)``."""
    b = _bits(bits)
    if b.size % 2:
        raise ValueError("QPSK needs an even number of bits")
    i = 1.0 - 2.0 * b[0::2]
    q = 1.0 - 2.0 * b[1::2]
    symbols: NDArray[np.complex128] = (i + 1j * q) * _INV_SQRT2
    return symbols


def qpsk_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision QPSK demapping: bit is 1 where I (or Q) is negative; exactly 0 gives bit 0."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    out = np.empty(2 * s.size, dtype=np.uint8)
    out[0::2] = s.real < 0
    out[1::2] = s.imag < 0
    return out


def _groups(bits: ArrayLike, k: int, name: str) -> NDArray[np.int64]:
    b = _bits(bits)
    if b.size % k:
        raise ValueError(f"{name} needs a multiple of {k} bits")
    groups = b.reshape(-1, k).astype(np.int64)
    return groups


def _bits_of(labels: NDArray[np.int64], k: int) -> NDArray[np.uint8]:
    shifts = np.arange(k - 1, -1, -1)
    return ((labels[:, None] >> shifts) & 1).astype(np.uint8).reshape(-1)


def psk8_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded 8-PSK: label ``m`` (3 bits, MSB first) to ``exp(j*pi*p/4)`` where
    ``p ^ (p >> 1) == m`` (conventions: Bits and symbols)."""
    g = _groups(bits, 3, "8-PSK")
    m = 4 * g[:, 0] + 2 * g[:, 1] + g[:, 2]
    p = m ^ (m >> 1) ^ (m >> 2)
    symbols = np.asarray(np.exp(1j * (np.pi / 4) * p), dtype=np.complex128)
    return symbols


def psk8_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision 8-PSK: the nearest point's label; 0 decides ``000``."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    p = np.mod(np.floor(np.arctan2(s.imag, s.real) / (np.pi / 4) + 0.5), 8).astype(np.int64)
    return _bits_of(p ^ (p >> 1), 3)


def qam16_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded 16-QAM: ``I`` from ``(b0, b1)``, ``Q`` from ``(b2, b3)``, each
    ``(1 - 2*first)*(3 - 2*second)``, over ``sqrt(10)`` (conventions: Bits and symbols)."""
    g = _groups(bits, 4, "16-QAM").astype(np.float64)
    i = (1 - 2 * g[:, 0]) * (3 - 2 * g[:, 1])
    q = (1 - 2 * g[:, 2]) * (3 - 2 * g[:, 3])
    symbols = np.asarray((i + 1j * q) * _INV_SQRT10, dtype=np.complex128)
    return symbols


def qam16_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision 16-QAM: per component, first bit ``v < 0``, second ``|v| < 2/sqrt(10)``."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    out = np.empty(4 * s.size, dtype=np.uint8)
    out[0::4] = s.real < 0
    out[1::4] = np.abs(s.real) < _QAM16_THRESHOLD
    out[2::4] = s.imag < 0
    out[3::4] = np.abs(s.imag) < _QAM16_THRESHOLD
    return out
