"""Block synchronization estimators: symbol timing, QPSK carrier frequency and phase.

Definitions are in docs/conventions.md (Synchronization) and
docs/adr/0008-block-synchronization.md.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count


def _complex(x: ArrayLike, what: str, minimum: int) -> NDArray[np.complex128]:
    a = np.asarray(x)
    if a.ndim != 1:
        raise ValueError(f"{what} must be one-dimensional")
    if a.size < minimum:
        raise ValueError(f"{what} needs at least {minimum}")
    a = np.asarray(a, dtype=np.complex128)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{what} must be finite")
    return a


def _arg(s: complex) -> float:
    """Phase in ``(-pi, pi]``; 0 for an exact zero (atan2 gives -pi for a -0.0 imaginary part)."""
    if s == 0:
        return 0.0
    a = math.atan2(s.imag, s.real)
    return math.pi if a == -math.pi else a


def timing_offset(samples: ArrayLike, samples_per_symbol: int) -> float:
    """Oerder-Meyr symbol timing estimate in samples, in ``[0, sps)``."""
    sps = count(samples_per_symbol, "samples_per_symbol")
    if sps < 2:
        raise ValueError("samples_per_symbol must be at least 2")
    y = _complex(samples, "samples", 1)
    n = np.arange(y.size)
    s = complex(np.sum((y.real**2 + y.imag**2) * np.exp(-2j * np.pi * (n % sps) / sps)))
    tau = -sps * _arg(s) / (2 * math.pi)
    if tau < 0:
        tau += sps
    return 0.0 if tau >= sps else tau


def qpsk_frequency_offset(symbols: ArrayLike, symbol_rate: float) -> float:
    """Carrier frequency offset of QPSK symbols in Hz, in ``(-Rs/8, Rs/8]``."""
    if not 0 < symbol_rate < math.inf:
        raise ValueError("symbol_rate must be positive and finite")
    z = _complex(symbols, "symbols", 2)
    z2 = z * z
    w = z2 * z2
    s = complex(np.sum(w[1:] * np.conj(w[:-1])))
    return _arg(s) * symbol_rate / (8 * math.pi)


def qpsk_phase_offset(symbols: ArrayLike) -> float:
    """Carrier phase of QPSK symbols in radians, in ``(-pi/4, pi/4]``, modulo pi/2."""
    z = _complex(symbols, "symbols", 1)
    z2 = z * z
    w = z2 * z2
    return _arg(-complex(np.sum(w))) / 4
