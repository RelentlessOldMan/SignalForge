"""Convolution, upsampling and root-raised-cosine pulse shaping.

Definitions are in docs/conventions.md (Pulse shaping) and
docs/adr/0007-pulse-shaping-channel-evm.md.
"""

from __future__ import annotations

import math
from typing import cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count


def _vector(x: ArrayLike, what: str) -> NDArray[np.complex128] | NDArray[np.float64]:
    a = np.asarray(x)
    if a.ndim != 1 or a.size == 0:
        raise ValueError(f"{what} must be a non-empty 1-D array")
    if np.iscomplexobj(a):
        return np.asarray(a, dtype=np.complex128)
    return np.asarray(a, dtype=np.float64)


def convolve(x: ArrayLike, h: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Full linear convolution ``y[n] = sum h[k] x[n-k]``, length ``len(x) + len(h) - 1``."""
    y = np.convolve(_vector(x, "x"), _vector(h, "h"))
    return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def upsample(x: ArrayLike, factor: int) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Each sample followed by ``factor - 1`` zeros."""
    a = _vector(x, "x")
    if count(factor, "factor") < 1:
        raise ValueError("factor must be at least 1")
    y = np.zeros(a.size * factor, dtype=a.dtype)
    y[::factor] = a
    return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def rrc_taps(beta: float, samples_per_symbol: int, span_symbols: int) -> NDArray[np.float64]:
    """Root-raised-cosine taps, ``span * sps + 1`` of them, scaled to unit energy."""
    if not 0 <= beta <= 1:
        raise ValueError("beta must be in [0, 1]")
    sps = count(samples_per_symbol, "samples_per_symbol")
    span = count(span_symbols, "span_symbols")
    if sps < 1:
        raise ValueError("samples_per_symbol must be at least 1")
    if span < 2 or span % 2:
        raise ValueError("span_symbols must be even and at least 2")
    n = span * sps + 1
    h = np.empty(n)
    for i in range(n):
        t = (i - (n - 1) / 2) / sps
        if t == 0:
            h[i] = 1 - beta + 4 * beta / math.pi
        elif abs(4 * beta * abs(t) - 1) < 1e-9:
            a = math.pi / (4 * beta)
            h[i] = (
                beta
                / math.sqrt(2)
                * ((1 + 2 / math.pi) * math.sin(a) + (1 - 2 / math.pi) * math.cos(a))
            )
        else:
            num = math.sin(math.pi * t * (1 - beta)) + 4 * beta * t * math.cos(
                math.pi * t * (1 + beta)
            )
            h[i] = num / (math.pi * t * (1 - (4 * beta * t) ** 2))
    return np.asarray(h / math.sqrt(float(np.sum(h * h))), dtype=np.float64)


def pulse_shape(
    symbols: ArrayLike, taps: ArrayLike, samples_per_symbol: int
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``convolve(upsample(symbols, sps), taps)``; symbol ``k`` peaks at ``k*sps + (N-1)/2``."""
    return convolve(upsample(symbols, samples_per_symbol), taps)
