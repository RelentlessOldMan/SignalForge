"""Channel impairments: AWGN at a given Es/N0, frequency offset.

Definitions are in docs/conventions.md (Channel) and docs/adr/0007-pulse-shaping-channel-evm.md.
"""

from __future__ import annotations

import math
import numbers

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count, real


def awgn(
    samples: ArrayLike,
    es_n0_db: float,
    samples_per_symbol: int = 1,
    *,
    seed: int | np.random.Generator,
    signal_power: float | None = None,
) -> NDArray[np.complex128]:
    """Add complex Gaussian noise of variance ``P * sps / 10**(es_n0_db/10)``.

    ``P`` is ``signal_power``, or the measured mean ``|x|^2`` if not given.
    """
    x = np.asarray(samples)
    if x.ndim != 1 or x.size == 0 or not np.iscomplexobj(x):
        raise ValueError("samples must be a non-empty 1-D complex array")
    x = np.asarray(x, dtype=np.complex128)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if not math.isfinite(es_n0_db):
        raise ValueError("es_n0_db must be finite")
    sps = count(samples_per_symbol, "samples_per_symbol")
    if sps < 1:
        raise ValueError("samples_per_symbol must be at least 1")
    p = float(np.mean(np.abs(x) ** 2)) if signal_power is None else signal_power
    if not 0 < p < math.inf:
        raise ValueError("signal power must be positive and finite")
    rng = (
        seed
        if isinstance(seed, np.random.Generator)
        else np.random.default_rng(count(seed, "seed"))
    )
    try:
        variance = p * sps * 10 ** (-es_n0_db / 10)
    except OverflowError:
        variance = math.inf
    if not math.isfinite(variance):
        raise ValueError("es_n0_db is so low that the noise variance overflows")
    sigma = math.sqrt(variance / 2)
    noise = rng.standard_normal(x.size) + 1j * rng.standard_normal(x.size)
    return np.asarray(x + sigma * noise, dtype=np.complex128)


def frequency_offset(
    samples: ArrayLike, offset_hz: float, sample_rate: float, phase: float = 0.0
) -> NDArray[np.complex128]:
    """``x[n] * exp(j*(2*pi*offset_hz*n/sample_rate + phase))``."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if not 0 < sample_rate < math.inf:
        raise ValueError("sample_rate must be positive and finite")
    if not (math.isfinite(offset_hz) and math.isfinite(phase)):
        raise ValueError("offset_hz and phase must be finite")
    arg = 2.0 * np.pi * offset_hz * (np.arange(x.size) / sample_rate) + phase
    return np.asarray(x * np.exp(1j * arg), dtype=np.complex128)


def phase_noise(
    samples: ArrayLike,
    linewidth_hz: float,
    sample_rate: float,
    *,
    seed: int | np.random.Generator,
) -> NDArray[np.complex128]:
    """Wiener phase noise: ``x[n] * exp(j*phi[n])``, ``phi[0] = 0``, Gaussian increments of
    variance ``2*pi*linewidth_hz/sample_rate`` (conventions: Channel, Phase noise)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if not 0 < sample_rate < math.inf:
        raise ValueError("sample_rate must be positive and finite")
    if not 0 <= linewidth_hz < math.inf:
        raise ValueError("linewidth_hz must be finite and not negative")
    rng = (
        seed
        if isinstance(seed, np.random.Generator)
        else np.random.default_rng(count(seed, "seed"))
    )
    sigma = math.sqrt(2 * math.pi * linewidth_hz / sample_rate)
    steps = sigma * rng.standard_normal(max(x.size - 1, 0))
    phi = np.concatenate([[0.0], np.cumsum(steps)])[: x.size]
    return np.asarray(x * np.exp(1j * phi), dtype=np.complex128)


def multipath(samples: ArrayLike, delays: ArrayLike, gains: ArrayLike) -> NDArray[np.complex128]:
    """Static tapped delay line: ``y[n] = sum_i gains[i] * x[n - delays[i]]``, as long as the
    input (conventions: Channel, Multipath)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    d = np.asarray(delays)
    g = np.asarray(gains)
    if d.ndim != 1 or g.ndim != 1 or d.size != g.size or d.size == 0:
        raise ValueError("delays and gains must be one-dimensional, of equal non-zero length")
    lags = [count(v, "delays") for v in d.tolist()]
    if not np.issubdtype(g.dtype, np.number) or g.dtype == np.bool_:
        raise ValueError("gains must be numbers")
    taps = g.astype(np.complex128)
    if not np.all(np.isfinite(taps)):
        raise ValueError("gains must be finite")
    y = np.zeros(x.size, dtype=np.complex128)
    for lag, tap in zip(lags, taps, strict=True):
        if lag < x.size:
            y[lag:] += tap * x[: x.size - lag]
    return y


_FD_BETA = 8.0
_FD_NORM = float(np.i0(_FD_BETA))


def fractional_delay(
    samples: ArrayLike, delay: float, *, half_width: int = 16
) -> NDArray[np.complex128]:
    """Delay by ``delay`` samples through a Kaiser-windowed sinc of ``2*half_width`` taps,
    as long as the input (conventions: Channel, Fractional delay)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    d = real(delay, "delay")
    h = count(half_width, "half_width")
    if h < 1:
        raise ValueError("half_width must be at least 1")
    return _read_at(np.asarray(x, dtype=np.complex128), np.arange(x.size, dtype=np.float64) - d, h)


def _read_at(x: NDArray[np.complex128], pos: NDArray[np.float64], h: int) -> NDArray[np.complex128]:
    """``z(t)`` at each position through the fractional-delay kernel, the taps summed in order."""
    n = x.size
    y = np.zeros(pos.size, dtype=np.complex128)
    base = np.floor(pos)
    # the kernel depends on the sample only through its fraction, which takes few distinct
    # values: evaluate it once per fraction (the same arithmetic) and gather
    frac, which = np.unique(pos - base, return_inverse=True)
    on_grid = frac == 0
    norm = _FD_NORM
    for j in range(-h + 1, h + 1):
        t = frac - j
        with np.errstate(invalid="ignore", divide="ignore"):
            s = np.where(t == 0, 1.0, np.sin(math.pi * t) / (math.pi * t))
        s = np.where(on_grid & (t != 0), 0.0, s)
        w = np.i0(_FD_BETA * np.sqrt(np.maximum(1 - (t / h) ** 2, 0.0))) / norm
        tap = np.where(np.abs(t) < h, s * w, 0.0)[which]
        m = base + j
        valid = (m >= 0) & (m < n)
        if valid.any():
            y[valid] += tap[valid] * x[m[valid].astype(np.int64)]
    return y


def clock_offset(samples: ArrayLike, ppm: float, *, half_width: int = 16) -> NDArray[np.complex128]:
    """The input read every ``1 + ppm/1e6`` samples through the fractional-delay kernel: a
    receiver whose sample clock is off by ``ppm`` (conventions: Channel, Sample clock offset)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    e = real(ppm, "ppm")
    if abs(e) > 1e5:
        raise ValueError("ppm must be within 1e5")
    h = count(half_width, "half_width")
    if h < 1:
        raise ValueError("half_width must be at least 1")
    r = 1 + e / 1e6
    pos = np.arange(int((x.size - 1) / r) + 2, dtype=np.float64) * r if x.size else np.zeros(0)
    pos = pos[pos <= x.size - 1]
    return _read_at(np.asarray(x, dtype=np.complex128), pos, h)


def rician_fading(
    samples: ArrayLike,
    k_factor: float,
    block_length: int,
    *,
    seed: int | np.random.Generator,
) -> NDArray[np.complex128]:
    """Flat block fading: each block of ``block_length`` samples times one Rician gain of unit
    mean power, ``k_factor = 0`` for Rayleigh (conventions: Channel, Block fading)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if isinstance(k_factor, bool | np.bool_) or not isinstance(k_factor, numbers.Real):
        raise ValueError("k_factor must be a number")
    k = float(k_factor)
    if not k >= 0:
        raise ValueError("k_factor must not be negative or NaN")
    length = count(block_length, "block_length")
    if length < 1:
        raise ValueError("block_length must be at least 1")
    rng = (
        seed
        if isinstance(seed, np.random.Generator)
        else np.random.default_rng(count(seed, "seed"))
    )
    if math.isinf(k):
        return np.asarray(x, dtype=np.complex128).copy()
    blocks = -(-x.size // length)
    ab = rng.standard_normal((blocks, 2))
    scatter = (ab[:, 0] + 1j * ab[:, 1]) / math.sqrt(2)
    g = math.sqrt(k / (k + 1)) + math.sqrt(1 / (k + 1)) * scatter
    return np.asarray(x * np.repeat(g, length)[: x.size], dtype=np.complex128)


def _interpolate(y: list[complex], t: float, half_width: int) -> complex:
    """``z(t)`` through the fractional-delay kernel (conventions: Synchronization, Tracking
    loops); the same arithmetic as ``fractional_delay``."""
    h = half_width
    b = math.floor(t)
    f = t - b
    tt = f - np.arange(-h + 1, h + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        s = np.where(tt == 0, 1.0, np.sin(math.pi * tt) / (math.pi * tt))
    if f == 0:
        s = np.where(tt != 0, 0.0, s)
    w = np.i0(_FD_BETA * np.sqrt(np.maximum(1 - (tt / h) ** 2, 0.0))) / _FD_NORM
    taps = np.where(np.abs(tt) < h, s * w, 0.0).tolist()
    acc = 0j
    for i in range(max(0, h - 1 - b), min(2 * h, len(y) + h - 1 - b)):
        acc += taps[i] * y[b - h + 1 + i]
    return acc


def _imbalance_gain(gain_db: float, phase: float) -> float:
    if not (math.isfinite(gain_db) and math.isfinite(phase)):
        raise ValueError("gain_db and phase must be finite")
    try:
        g = float(10.0 ** (gain_db / 20.0))
    except OverflowError:
        g = math.inf
    if not 0 < g < math.inf:
        raise ValueError("gain_db is out of range")
    return g


def iq_imbalance(samples: ArrayLike, gain_db: float, phase: float) -> NDArray[np.complex128]:
    """``I + j*g*(Q*cos(phase) + I*sin(phase))``, ``g = 10**(gain_db/20)``: the error on the Q
    branch (conventions: Channel, IQ imbalance)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    g = _imbalance_gain(gain_db, phase)
    i, q = x.real.astype(np.float64), x.imag.astype(np.float64)
    return np.asarray(
        i + 1j * (q * (g * math.cos(phase)) + i * (g * math.sin(phase))), np.complex128
    )


def iq_image_rejection_db(gain_db: float, phase: float) -> float:
    """Tone-to-image power ratio in dB of ``iq_imbalance(gain_db, phase)``; ``inf`` with no
    imbalance (conventions: Channel, Image rejection)."""
    g = _imbalance_gain(gain_db, phase)
    num = 1 + g * g + 2 * g * math.cos(phase)
    den = 1 + g * g - 2 * g * math.cos(phase)
    return math.inf if den <= 0 else 10.0 * math.log10(num / den)


def dc_offset(samples: ArrayLike, offset: complex) -> NDArray[np.complex128]:
    """``samples + offset`` (conventions: Channel, DC offset)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    c = complex(offset)
    if not (math.isfinite(c.real) and math.isfinite(c.imag)):
        raise ValueError("offset must be finite")
    return np.asarray(x + c, dtype=np.complex128)
