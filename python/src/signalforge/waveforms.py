"""Waveform generators: tones and PRBS. Definitions in docs/conventions.md."""

from __future__ import annotations

import numpy as np

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
) -> np.ndarray:
    """``amplitude * exp(j(2*pi*f*n/fs + phase))``, or ``amplitude * cos(...)`` when not complex.

    ``amplitude`` is the peak amplitude and ``phase`` is in radians.
    """
    if not sample_rate > 0:
        raise ValueError("sample_rate must be positive")
    if num_samples < 0:
        raise ValueError("num_samples must be non-negative")
    arg = 2.0 * np.pi * frequency * (np.arange(num_samples) / sample_rate) + phase
    if complex:
        return amplitude * np.exp(1j * arg)
    return amplitude * np.cos(arg)


def prbs(order: int, num_bits: int, *, seed: int | None = None, invert: bool = False) -> np.ndarray:
    """Maximal-length PRBS bits (``uint8``) for the O.150 polynomial of the given order.

    The sequence satisfies ``a[i] = a[i-m] XOR a[i-k]`` for ``x^m + x^k + 1``. ``seed`` gives the
    first ``m`` bits, first bit in the most significant position; the default is all ones.
    """
    if order not in PRBS_TAPS:
        raise ValueError(f"unsupported PRBS order {order}; supported: {sorted(PRBS_TAPS)}")
    if num_bits < 0:
        raise ValueError("num_bits must be non-negative")
    m, k = order, PRBS_TAPS[order]
    full = (1 << m) - 1
    state = full if seed is None else seed
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
