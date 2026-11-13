"""Convolution, upsampling, root-raised-cosine pulse shaping, FIR design and FIR filtering.

Definitions are in docs/conventions.md (Pulse shaping, FIR filters),
docs/adr/0007-pulse-shaping-channel-evm.md and docs/adr/0010-fir-design-streaming.md.
"""

from __future__ import annotations

import math
from typing import cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count, real
from .spectral import window as _window


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


def _fir_design(
    num_taps: int,
    ideal: list[tuple[float, float]],
    reference: float,
    window: str,
    beta: float | None,
) -> NDArray[np.float64]:
    """``sum sign * 2nu sinc(2nu t)`` over ``ideal`` (pairs ``(sign, nu)``), windowed, then scaled
    to unit zero-phase gain at the normalized ``reference`` frequency."""
    n = count(num_taps, "num_taps")
    if n < 1:
        raise ValueError("num_taps must be at least 1")
    t = np.arange(n, dtype=np.float64) - (n - 1) / 2
    d = np.zeros(n)
    for sign, nu in ideal:
        d += sign * 2 * nu * np.sinc(2 * nu * t)
    h = d * _window(window, n, symmetric=True, beta=beta)
    gain = float(np.sum(h * np.cos(2 * np.pi * reference * t)))
    if not abs(gain) > 1e-6 * float(np.sum(np.abs(h))):
        raise ValueError("too few taps: the design has almost no gain at its reference frequency")
    return np.asarray(h / gain, dtype=np.float64)


def _rate(sample_rate: float) -> float:
    fs = real(sample_rate, "sample_rate")
    if fs <= 0:
        raise ValueError("sample_rate must be positive")
    return fs


def _band_edge(f: float, fs: float, what: str) -> float:
    """``f/fs`` for a frequency strictly between 0 and ``fs/2``."""
    f = real(f, what)
    if not 0 < f < fs / 2:
        raise ValueError(f"{what} must be between 0 and sample_rate/2")
    return f / fs


def fir_lowpass(
    num_taps: int,
    cutoff: float,
    sample_rate: float,
    window: str = "hamming",
    beta: float | None = None,
) -> NDArray[np.float64]:
    """Windowed-sinc low-pass taps with unit gain at DC."""
    nu = _band_edge(cutoff, _rate(sample_rate), "cutoff")
    return _fir_design(num_taps, [(1.0, nu)], 0.0, window, beta)


def fir_highpass(
    num_taps: int,
    cutoff: float,
    sample_rate: float,
    window: str = "hamming",
    beta: float | None = None,
) -> NDArray[np.float64]:
    """Windowed-sinc high-pass taps with unit gain at ``sample_rate/2``; ``num_taps`` odd."""
    nu = _band_edge(cutoff, _rate(sample_rate), "cutoff")
    if count(num_taps, "num_taps") % 2 == 0:
        raise ValueError("a high-pass needs an odd num_taps")
    return _fir_design(num_taps, [(1.0, 0.5), (-1.0, nu)], 0.5, window, beta)


def fir_bandpass(
    num_taps: int,
    low: float,
    high: float,
    sample_rate: float,
    window: str = "hamming",
    beta: float | None = None,
) -> NDArray[np.float64]:
    """Windowed-sinc band-pass taps with unit gain at the band center ``(low + high)/2``."""
    fs = _rate(sample_rate)
    lo = _band_edge(low, fs, "low")
    hi = _band_edge(high, fs, "high")
    if lo >= hi:
        raise ValueError("low must be below high")
    return _fir_design(num_taps, [(1.0, hi), (-1.0, lo)], (lo + hi) / 2, window, beta)


def kaiser_parameters(
    attenuation_db: float, transition_width: float, sample_rate: float
) -> tuple[int, float]:
    """``(num_taps, beta)`` for a Kaiser-window design, from Kaiser's formulas (conventions)."""
    fs = _rate(sample_rate)
    a = real(attenuation_db, "attenuation_db")
    if a <= 0:
        raise ValueError("attenuation_db must be positive")
    dw = 2 * math.pi * _band_edge(transition_width, fs, "transition_width")
    if a > 50:
        beta = 0.1102 * (a - 8.7)
    elif a >= 21:
        beta = 0.5842 * (a - 21) ** 0.4 + 0.07886 * (a - 21)
    else:
        beta = 0.0
    order = max(0, math.ceil((a - 8) / (2.285 * dw)))
    if order >= 2**31 - 1:
        raise ValueError("transition_width is too narrow for any filter length")
    return order + 1, beta


def _taps(taps: ArrayLike) -> NDArray[np.float64]:
    h = np.asarray(taps)
    if h.ndim != 1 or h.size == 0 or np.iscomplexobj(h):
        raise ValueError("taps must be a non-empty 1-D real array")
    h = np.array(h, dtype=np.float64)  # a copy: callers may change theirs
    if not np.all(np.isfinite(h)):
        raise ValueError("taps must be finite")
    return h


def fir_response(
    taps: ArrayLike, frequencies: ArrayLike, sample_rate: float
) -> NDArray[np.complex128]:
    """Complex response ``H(f) = sum h[n] exp(-j 2 pi f n / fs)`` at each frequency."""
    h = _taps(taps)
    fs = _rate(sample_rate)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.ndim != 1 or not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be a finite 1-D array")
    n = np.arange(h.size, dtype=np.float64)
    return np.asarray(np.exp(-2j * np.pi * np.outer(f / fs, n)) @ h, dtype=np.complex128)


class FirFilter:
    """Causal direct-form FIR filter that keeps its state across chunks (conventions: FIR filters).

    The first non-empty chunk fixes the filter as real or complex until :meth:`reset`.
    """

    def __init__(self, taps: ArrayLike) -> None:
        self._h = _taps(taps)
        self._complex: bool | None = None
        self._state: NDArray[np.complex128] | NDArray[np.float64] = np.zeros(0)

    @property
    def taps(self) -> NDArray[np.float64]:
        """A copy of the taps."""
        return self._h.copy()

    def reset(self) -> None:
        """Forget every sample seen, as if new."""
        self._complex = None
        self._state = np.zeros(0)

    def process(self, chunk: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
        """The next ``len(chunk)`` output samples."""
        a = np.asarray(chunk)
        if a.ndim != 1:
            raise ValueError("chunk must be a 1-D array")
        is_complex = bool(np.iscomplexobj(a))
        x = np.asarray(a, dtype=np.complex128 if is_complex else np.float64)
        if x.size == 0:
            empty = np.zeros(0, dtype=np.complex128 if self._complex else np.float64)
            return cast("NDArray[np.complex128] | NDArray[np.float64]", empty)
        if self._complex is None:
            self._complex = is_complex
            self._state = cast(
                "NDArray[np.complex128] | NDArray[np.float64]",
                np.zeros(self._h.size - 1, dtype=x.dtype),
            )
        elif self._complex != is_complex:
            kind = "complex" if self._complex else "real"
            raise ValueError(f"this filter takes {kind} samples until reset()")
        ext = np.concatenate([self._state, x])
        y = np.convolve(ext, self._h, mode="valid")
        self._state = ext[ext.size - (self._h.size - 1) :]
        return cast("NDArray[np.complex128] | NDArray[np.float64]", y)
