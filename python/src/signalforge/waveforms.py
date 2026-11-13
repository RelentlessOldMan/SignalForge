"""Waveform generators: tones, multitones, chirps, pulse trains and PRBS. Definitions in
docs/conventions.md."""

from __future__ import annotations

import math
import operator

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count as _count
from ._checks import real

#: ITU-T O.150 PRBS polynomials ``x^m + x^k + 1`` as ``order -> k``.
PRBS_TAPS: dict[int, int] = {7: 6, 9: 5, 11: 9, 15: 14, 20: 3, 23: 18, 31: 28}


def tone(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
    *,
    complex: bool = True,
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``amplitude * exp(j(2*pi*f*n/fs + phase))``, or ``amplitude * cos(...)`` when not complex.

    ``amplitude`` is the peak amplitude and ``phase`` is in radians.
    """
    if not 0 < sample_rate < math.inf:
        raise ValueError("sample_rate must be positive and finite")
    num_samples = _count(num_samples, "num_samples")
    frequency, amplitude = real(frequency, "frequency"), real(amplitude, "amplitude")
    phase = real(phase, "phase")
    arg = 2.0 * np.pi * frequency * (np.arange(num_samples) / sample_rate) + phase
    if complex:
        return np.asarray(amplitude * np.exp(1j * arg), dtype=np.complex128)
    return np.asarray(amplitude * np.cos(arg), dtype=np.float64)


def _finite_vector(v: ArrayLike, what: str) -> NDArray[np.float64]:
    a = np.asarray(v)
    if a.ndim != 1 or np.iscomplexobj(a) or a.dtype == np.bool_:
        raise ValueError(f"{what} must be a 1-D real array")
    a = np.asarray(a, dtype=np.float64)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{what} must be finite")
    return a


def multitone(
    sample_rate: float,
    num_samples: int,
    frequencies: ArrayLike,
    amplitudes: ArrayLike | None = None,
    phases: ArrayLike | None = None,
    *,
    complex: bool = True,
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """The sum of one :func:`tone` per frequency (conventions: Tones, Multitone)."""
    f = _finite_vector(frequencies, "frequencies")
    if f.size == 0:
        raise ValueError("frequencies needs at least one value")
    a = np.ones(f.size) if amplitudes is None else _finite_vector(amplitudes, "amplitudes")
    p = np.zeros(f.size) if phases is None else _finite_vector(phases, "phases")
    if a.size != f.size or p.size != f.size:
        raise ValueError("amplitudes and phases need one value per frequency")
    out = tone(sample_rate, num_samples, f[0], a[0], p[0], complex=complex)
    for k in range(1, f.size):
        out = out + tone(sample_rate, num_samples, f[k], a[k], p[k], complex=complex)
    return out


def newman_phases(count: int) -> NDArray[np.float64]:
    """Newman's low-crest-factor phases ``pi * k**2 / count`` for ``k = 0 .. count - 1``."""
    n = _count(count, "count")
    if n < 1:
        raise ValueError("count must be at least 1")
    k = np.arange(n, dtype=np.float64)
    return np.asarray(np.pi * k * k / n, dtype=np.float64)


def chirp(
    sample_rate: float,
    num_samples: int,
    start: float,
    stop: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
    *,
    complex: bool = True,
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Linear chirp from ``start`` Hz at the first sample to ``stop`` Hz at ``num_samples/fs``
    (conventions: Tones, Linear chirp)."""
    fs = real(sample_rate, "sample_rate")
    if fs <= 0:
        raise ValueError("sample_rate must be positive")
    n = _count(num_samples, "num_samples")
    f0, f1 = real(start, "start"), real(stop, "stop")
    amp, ph = real(amplitude, "amplitude"), real(phase, "phase")
    t = np.arange(n, dtype=np.float64) / fs
    rate = (f1 - f0) / (2 * (n / fs)) if n else 0.0
    arg = 2.0 * np.pi * (f0 * t + rate * (t * t)) + ph
    if complex:
        return np.asarray(amp * np.exp(1j * arg), dtype=np.complex128)
    return np.asarray(amp * np.cos(arg), dtype=np.float64)


def _integer(value: int, what: str) -> int:
    if isinstance(value, bool | np.bool_):
        raise ValueError(f"{what} must be an integer")
    try:
        return operator.index(value)
    except TypeError:
        raise ValueError(f"{what} must be an integer") from None


def pulse_train(
    num_samples: int, period: int, width: int, amplitude: float = 1.0, delay: int = 0
) -> NDArray[np.float64]:
    """Rectangular pulses, in whole samples: ``amplitude`` where ``(n - delay) mod period < width``
    (conventions: Tones, Pulse train)."""
    n = _count(num_samples, "num_samples")
    p = _count(period, "period")
    w = _count(width, "width")
    d = _integer(delay, "delay")
    amp = real(amplitude, "amplitude")
    if p < 1:
        raise ValueError("period must be at least 1")
    if w > p:
        raise ValueError("width must be at most period")
    on = np.mod(np.arange(n, dtype=np.int64) - d, p) < w
    return np.where(on, amp, 0.0).astype(np.float64)


def prbs(
    order: int, num_bits: int, *, seed: int | None = None, invert: bool = False
) -> NDArray[np.uint8]:
    """Maximal-length PRBS bits (``uint8``) for the O.150 polynomial of the given order.

    The sequence satisfies ``a[i] = a[i-m] XOR a[i-k]`` for ``x^m + x^k + 1``. ``seed`` gives the
    first ``m`` bits, first bit in the most significant position; the default is all ones.
    """
    order = _count(order, "order")
    num_bits = _count(num_bits, "num_bits")
    if order not in PRBS_TAPS:
        raise ValueError(f"unsupported PRBS order {order}; supported: {sorted(PRBS_TAPS)}")
    m, k = order, PRBS_TAPS[order]
    full = (1 << m) - 1
    state = full if seed is None else _count(seed, "seed")
    if not 0 < state <= full:
        raise ValueError(f"seed must be in 1..{full}")

    period = full
    count = min(num_bits, period)
    out = np.empty(count, dtype=np.uint8)
    # state holds the last m bits, oldest (a[i-m]) in the most significant position.
    for i in range(count):
        bit = (state >> (m - 1)) & 1
        out[i] = bit
        new = bit ^ ((state >> (k - 1)) & 1)  # a[i] = a[i-m] ^ a[i-k], for the bit m ahead
        state = ((state << 1) & full) | new
    if num_bits > period:
        out = np.resize(out, num_bits)
    if invert:
        out ^= 1
    return out
