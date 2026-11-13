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
    sigma = math.sqrt(p * sps / 10 ** (es_n0_db / 10) / 2)
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
