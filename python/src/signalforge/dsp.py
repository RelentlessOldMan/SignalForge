"""Convolution, upsampling, root-raised-cosine pulse shaping, FIR and IIR design and filtering.

Definitions are in docs/conventions.md (Pulse shaping, FIR filters, IIR filters),
docs/adr/0007-pulse-shaping-channel-evm.md, docs/adr/0010-fir-design-streaming.md and
docs/adr/0014-iir-filters.md.
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Callable
from typing import Any, cast

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


def _sos(sos: ArrayLike) -> NDArray[np.float64]:
    """A copy of a cascade of second-order sections, each row divided by its ``a0``."""
    s = np.asarray(sos)
    if s.ndim != 2 or s.shape[0] == 0 or s.shape[1] != 6 or np.iscomplexobj(s):
        raise ValueError(
            "sos must be a real array of shape (sections, 6) with at least one section"
        )
    s = np.array(s, dtype=np.float64)
    if not np.all(np.isfinite(s)):
        raise ValueError("sos must be finite")
    if np.any(s[:, 3] == 0):
        raise ValueError("every section needs a0 != 0")
    return np.asarray(s / s[:, 3:4], dtype=np.float64)


def _order(order: int) -> int:
    n = count(order, "order")
    if n < 1:
        raise ValueError("order must be at least 1")
    return n


def _theta(i: int, n: int) -> float:
    return math.pi / 2 + math.pi * (2 * i + 1) / (2 * n)


def _butterworth(order: int, cutoff: float, sample_rate: float, high: bool) -> NDArray[np.float64]:
    n = _order(order)
    return _cascade(n, cutoff, sample_rate, high, lambda i: cmath.exp(1j * _theta(i, n)))


def _chebyshev1(
    order: int, ripple_db: float, cutoff: float, sample_rate: float, high: bool
) -> NDArray[np.float64]:
    n = _order(order)
    r = real(ripple_db, "ripple_db")
    if r <= 0:
        raise ValueError("ripple_db must be positive")
    mu = math.asinh(1 / math.sqrt(10 ** (r / 10) - 1)) / n
    sh, ch = math.sinh(mu), math.cosh(mu)
    rows = _cascade(
        n,
        cutoff,
        sample_rate,
        high,
        lambda i: complex(sh * math.cos(_theta(i, n)), ch * math.sin(_theta(i, n))),
    )
    if n % 2 == 0:
        rows[0, :3] *= 10 ** (-r / 20)  # the ripple's low point at DC (or fs/2)
    return rows


def _cascade(
    n: int, cutoff: float, sample_rate: float, high: bool, prototype: Callable[[int], complex]
) -> NDArray[np.float64]:
    """Sections from the analog prototype poles (cutoff 1): low-pass or high-pass, prewarped
    bilinear transform, Butterworth section order and unit gain at DC or fs/2."""
    fs = _rate(sample_rate)
    k = math.tan(math.pi * _band_edge(cutoff, fs, "cutoff"))
    zero = 1.0 if high else -1.0  # zeros at z = 1 (high-pass) or z = -1 (low-pass)
    rows: list[list[float]] = []

    def pole(i: int) -> complex:
        """Prototype pole ``i`` scaled to the prewarped cutoff, through the bilinear transform."""
        s = k / prototype(i) if high else k * prototype(i)
        return (1 + s) / (1 - s)

    if n % 2:
        p = pole((n - 1) // 2).real
        g = (1 + p) / 2 if high else (1 - p) / 2  # unit gain at fs/2 or DC
        rows.append([g, -zero * g, 0.0, 1.0, -p, 0.0])
    for i in range(n // 2 - 1, -1, -1):
        z = pole(i)
        a1, a2 = -2 * z.real, abs(z) ** 2
        g = (1 - zero * a1 + a2) / 4  # unit gain at the reference z = -zero
        rows.append([g, -2 * zero * g, g, 1.0, a1, a2])
    return np.array(rows, dtype=np.float64)


def butterworth_lowpass(order: int, cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """Butterworth low-pass by the bilinear transform, as second-order sections (conventions: IIR
    filters)."""
    return _butterworth(order, cutoff, sample_rate, high=False)


def butterworth_highpass(order: int, cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """Butterworth high-pass by the bilinear transform, as second-order sections (conventions: IIR
    filters)."""
    return _butterworth(order, cutoff, sample_rate, high=True)


def chebyshev1_lowpass(
    order: int, ripple_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type I low-pass by the bilinear transform, as second-order sections: pass-band
    ripple ``ripple_db``, which ``cutoff`` ends (conventions: IIR filters)."""
    return _chebyshev1(order, ripple_db, cutoff, sample_rate, high=False)


def chebyshev1_highpass(
    order: int, ripple_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type I high-pass by the bilinear transform, as second-order sections: pass-band
    ripple ``ripple_db``, which starts at ``cutoff`` (conventions: IIR filters)."""
    return _chebyshev1(order, ripple_db, cutoff, sample_rate, high=True)


def _butterworth_band(
    order: int, low: float, high: float, sample_rate: float, stop: bool
) -> NDArray[np.float64]:
    n = _order(order)
    fs = _rate(sample_rate)
    lo = math.tan(math.pi * _band_edge(low, fs, "low"))
    hi = math.tan(math.pi * _band_edge(high, fs, "high"))
    if lo >= hi:
        raise ValueError("low must be below high")
    w2, bw = lo * hi, hi - lo  # center squared and width, prewarped
    rows: list[list[float]] = []

    def section(sigma: float, m: float) -> None:
        """Analog section with poles at ``s`` and its conjugate (``sigma = Re s``, ``m = |s|^2``)
        through the bilinear transform ``s = (1 - z^-1)/(1 + z^-1)``, divided by ``a0``."""
        a0 = 1 - 2 * sigma + m
        if stop:  # (s^2 + w2) / ...
            b = [(1 + w2) / a0, 2 * (w2 - 1) / a0, (1 + w2) / a0]
        else:  # bw * s / ...
            b = [bw / a0, 0.0, -bw / a0]
        rows.append([*b, 1.0, 2 * (m - 1) / a0, (1 + 2 * sigma + m) / a0])

    if n % 2:  # the real pole -1 maps to s^2 + bw*s + w2 in both transforms
        section(-bw / 2, w2)
    for i in range(n // 2 - 1, -1, -1):
        p = cmath.exp(1j * (math.pi / 2 + math.pi * (2 * i + 1) / (2 * n)))
        c = bw / p if stop else bw * p  # the pole's two images: roots of s^2 - c*s + w2
        r = cmath.sqrt(c * c - 4 * w2)
        for s in sorted([(c + r) / 2, (c - r) / 2], key=abs):
            section(s.real, abs(s) ** 2)
    return np.array(rows, dtype=np.float64)


def butterworth_bandpass(
    order: int, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Butterworth band-pass from the low-pass prototype of that order, by the bilinear transform,
    as ``order`` second-order sections (conventions: IIR filters)."""
    return _butterworth_band(order, low, high, sample_rate, stop=False)


def butterworth_bandstop(
    order: int, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Butterworth band-stop from the low-pass prototype of that order, by the bilinear transform,
    as ``order`` second-order sections (conventions: IIR filters)."""
    return _butterworth_band(order, low, high, sample_rate, stop=True)


def sos_response(
    sos: ArrayLike, frequencies: ArrayLike, sample_rate: float
) -> NDArray[np.complex128]:
    """Complex response of a cascade of second-order sections at each frequency."""
    s = _sos(sos)
    fs = _rate(sample_rate)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.ndim != 1 or not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be a finite 1-D array")
    zi = np.exp(-2j * np.pi * f / fs)  # z^-1
    h = np.ones(f.size, dtype=np.complex128)
    for b0, b1, b2, a0, a1, a2 in s:
        h *= (b0 + zi * (b1 + zi * b2)) / (a0 + zi * (a1 + zi * a2))
    return h


class IirFilter:
    """Causal cascade of second-order sections that keeps its state across chunks (conventions:
    IIR filters).

    The first non-empty chunk fixes the filter as real or complex until :meth:`reset`.
    """

    def __init__(self, sos: ArrayLike) -> None:
        self._sos = _sos(sos)
        self._complex: bool | None = None
        self._state: list[list[Any]] = []

    @property
    def sections(self) -> NDArray[np.float64]:
        """A copy of the sections, each with ``a0 = 1``."""
        return self._sos.copy()

    def reset(self) -> None:
        """Forget every sample seen, as if new."""
        self._complex = None
        self._state = []

    def process(self, chunk: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
        """The next ``len(chunk)`` output samples."""
        a = np.asarray(chunk)
        if a.ndim != 1:
            raise ValueError("chunk must be a 1-D array")
        is_complex = bool(np.iscomplexobj(a))
        dtype = np.complex128 if is_complex else np.float64
        if a.size == 0:
            empty = np.zeros(0, dtype=np.complex128 if self._complex else np.float64)
            return cast("NDArray[np.complex128] | NDArray[np.float64]", empty)
        if self._complex is None:
            self._complex = is_complex
            self._state = [[0.0, 0.0] for _ in self._sos]
        elif self._complex != is_complex:
            kind = "complex" if self._complex else "real"
            raise ValueError(f"this filter takes {kind} samples until reset()")
        y: list[Any] = np.asarray(a, dtype=dtype).tolist()
        for (b0, b1, b2, _, a1, a2), st in zip(self._sos.tolist(), self._state, strict=True):
            s1, s2 = st  # transposed direct form II
            for i, v in enumerate(y):
                out = b0 * v + s1
                s1 = b1 * v - a1 * out + s2
                s2 = b2 * v - a2 * out
                y[i] = out
            st[0], st[1] = s1, s2
        return cast("NDArray[np.complex128] | NDArray[np.float64]", np.array(y, dtype=dtype))


def _steady_pass(sos: list[list[float]], y: list[Any]) -> None:
    """Runs the sections over ``y`` in place, each starting in its steady state for a constant
    input equal to the first sample it sees."""
    u = y[0]
    for b0, b1, b2, _, a1, a2 in sos:
        g = (b0 + b1 + b2) / (1 + a1 + a2)
        s2 = (b2 - a2 * g) * u  # transposed direct form II, as if u had always been the input
        s1 = (b1 - a1 * g) * u + s2
        for i, v in enumerate(y):
            out = b0 * v + s1
            s1 = b1 * v - a1 * out + s2
            s2 = b2 * v - a2 * out
            y[i] = out
        u = g * u


def zero_phase_filter(
    sos: ArrayLike, samples: ArrayLike, pad: int | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """The sections run forward, then backward, over the samples extended by ``pad`` samples of
    odd reflection at each end (default ``3·(2·sections + 1)``); zero phase, magnitude ``|H|²``
    (conventions: IIR filters)."""
    s = _sos(sos)
    if np.any(1 + s[:, 4] + s[:, 5] == 0):
        raise ValueError("every section needs 1 + a1 + a2 != 0 (no pole at z = 1)")
    x = _vector(samples, "samples")
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite: one non-finite sample spoils every output")
    p = 3 * (2 * s.shape[0] + 1) if pad is None else count(pad, "pad")
    if x.size <= p:
        raise ValueError("samples must be longer than pad")
    ext = np.concatenate([2 * x[0] - x[p:0:-1], x, 2 * x[-1] - x[-2 : -p - 2 : -1]])
    y: list[Any] = ext.tolist()
    rows = s.tolist()
    _steady_pass(rows, y)
    y.reverse()
    _steady_pass(rows, y)
    y.reverse()
    return cast(
        "NDArray[np.complex128] | NDArray[np.float64]", np.array(y[p : p + x.size], dtype=x.dtype)
    )


def _factors(up: int, down: int) -> tuple[int, int]:
    """``(up, down)`` checked and reduced by their greatest common divisor."""
    lu, md = count(up, "up"), count(down, "down")
    if lu < 1 or md < 1:
        raise ValueError("up and down must be at least 1")
    g = math.gcd(lu, md)
    return lu // g, md // g


def resample_taps(up: int, down: int) -> NDArray[np.float64]:
    """Default anti-aliasing taps for :func:`resample`: ``fir_lowpass(20R + 1, 1/(2R), 1)``,
    ``R = max(up, down)`` after reduction. Needs ``R > 1``."""
    r = max(_factors(up, down))
    if r == 1:
        raise ValueError("up and down reduce to 1/1, which needs no filter")
    return fir_lowpass(20 * r + 1, 1 / (2 * r), 1)


def resample(
    x: ArrayLike, up: int, down: int, taps: ArrayLike | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Resample by ``up/down`` with the delay removed: output ``m`` is at input time
    ``m * down / up`` (conventions: Resampling)."""
    a = _vector(x, "x")
    if a.size == 0:
        raise ValueError("x must be non-empty")
    lu, md = _factors(up, down)
    if taps is None:
        if lu == md == 1:
            return a.copy()
        h = resample_taps(lu, md)
    else:
        h = _taps(taps)
        if h.size % 2 == 0:
            raise ValueError("resample needs an odd number of taps")
    d = (h.size - 1) // 2
    n_out = -(-a.size * lu // md)
    full = np.convolve(upsample(a, lu), h)
    y = lu * full[d : d + n_out * md : md]
    return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def interpolate(
    x: ArrayLike, factor: int, taps: ArrayLike | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``resample(x, factor, 1, taps)``."""
    return resample(x, factor, 1, taps)


def decimate(
    x: ArrayLike, factor: int, taps: ArrayLike | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``resample(x, 1, factor, taps)``."""
    return resample(x, 1, factor, taps)
