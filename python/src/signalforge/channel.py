"""Channel impairments: AWGN at a given Es/N0, frequency offset.

Definitions are in docs/conventions.md (Channel) and docs/adr/0007-pulse-shaping-channel-evm.md.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count


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
