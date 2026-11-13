"""Symbol mapping. Definitions in docs/conventions.md."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

_INV_SQRT2 = 1.0 / np.sqrt(2.0)


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
