"""Synchronization: block estimators of symbol timing, QPSK carrier frequency and phase, and
tracking loops.

Definitions are in docs/conventions.md (Synchronization) and
docs/adr/0008-block-synchronization.md.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count, real
from .channel import _interpolate
from .modulation import _INV_SQRT10, _QAM16_THRESHOLD


def _complex(x: ArrayLike, what: str, minimum: int) -> NDArray[np.complex128]:
    a = np.asarray(x)
    if a.ndim != 1:
        raise ValueError(f"{what} must be one-dimensional")
    if a.size < minimum:
        raise ValueError(f"{what} needs at least {minimum}")
    a = np.asarray(a, dtype=np.complex128)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{what} must be finite")
    # The estimates do not depend on scale. Scaling by a power of two is exact and keeps |z|^4
    # from overflowing or underflowing.
    m = float(np.max(np.maximum(np.abs(a.real), np.abs(a.imag)), initial=0.0))
    if m > 0:
        e = -math.frexp(m)[1]
        a = np.ldexp(a.real, e) + 1j * np.ldexp(a.imag, e)
    return np.asarray(a, dtype=np.complex128)


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


def qpsk_block_phases(symbols: ArrayLike, block_symbols: int) -> NDArray[np.float64]:
    """QPSK carrier phase of each block of ``block_symbols`` symbols, unwrapped in steps of pi/2.

    The first block's phase is in ``(-pi/4, pi/4]``; each later one is moved by a multiple of pi/2
    to within pi/4 of the one before. A last, shorter block is included.
    """
    b = count(block_symbols, "block_symbols")
    if b < 1:
        raise ValueError("block_symbols must be at least 1")
    z = _complex(symbols, "symbols", 1)
    out = np.empty((z.size + b - 1) // b)
    for i in range(out.size):
        phi = qpsk_phase_offset(z[i * b : (i + 1) * b])
        if i > 0:
            phi += (math.pi / 2) * round((out[i - 1] - phi) / (math.pi / 2))
        out[i] = phi
    return out


def pi_loop_gains(
    loop_bandwidth: float, damping: float, detector_gain: float
) -> tuple[float, float]:
    """``(kp, ki)`` of a second-order loop with noise bandwidth ``loop_bandwidth`` per update
    (conventions: Synchronization, Tracking loops)."""
    bn = real(loop_bandwidth, "loop_bandwidth")
    z = real(damping, "damping")
    kd = real(detector_gain, "detector_gain")
    if not 0 < bn < 0.5:
        raise ValueError("loop_bandwidth must be in (0, 0.5)")
    if not z > 0 or not kd > 0:
        raise ValueError("damping and detector_gain must be positive")
    theta = bn / (z + 1 / (4 * z))
    d = 1 + 2 * z * theta + theta * theta
    return 4 * z * theta / d / kd, 4 * theta * theta / d / kd


@dataclass(frozen=True)
class TimingRecovery:
    """What a timing loop took: the symbols, their positions in samples, the detector output."""

    symbols: NDArray[np.complex128]
    positions: NDArray[np.float64]
    errors: NDArray[np.float64]


def gardner_timing(
    samples: ArrayLike,
    samples_per_symbol: int,
    kp: float,
    ki: float,
    *,
    start: float = 0.0,
    half_width: int = 8,
) -> TimingRecovery:
    """Gardner timing recovery: a PI loop on the step between symbols, reading between samples
    by the fractional-delay kernel (conventions: Synchronization, Tracking loops)."""
    sps = count(samples_per_symbol, "samples_per_symbol")
    if sps < 2:
        raise ValueError("samples_per_symbol must be at least 2")
    y = np.asarray(samples)
    if y.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    y = np.asarray(y, dtype=np.complex128)
    if not np.all(np.isfinite(y)):
        raise ValueError("samples must be finite")
    p = real(kp, "kp")
    i = real(ki, "ki")
    tau = real(start, "start")
    if p < 0 or i < 0 or tau < 0:
        raise ValueError("kp, ki and start must not be negative")
    h = count(half_width, "half_width")
    if h < 1:
        raise ValueError("half_width must be at least 1")
    ys: list[complex] = y.tolist()
    symbols: list[complex] = []
    positions: list[float] = []
    errors: list[float] = []
    v = 0.0
    while tau <= len(ys) - 1:
        z = _interpolate(ys, tau, h)
        e = 0.0
        if symbols:
            mid = _interpolate(ys, (positions[-1] + tau) / 2, h)
            delta = z - symbols[-1]
            e = mid.real * delta.real + mid.imag * delta.imag
        symbols.append(z)
        positions.append(tau)
        errors.append(e)
        v += i * e
        step = min(max(sps - p * e - v, sps / 2), 3 * sps / 2)
        tau += step
    return TimingRecovery(
        np.array(symbols, dtype=np.complex128),
        np.array(positions, dtype=np.float64),
        np.array(errors, dtype=np.float64),
    )


@dataclass(frozen=True)
class CarrierRecovery:
    """What a carrier loop gave: the corrected symbols, the phase used for each, the detector
    output."""

    symbols: NDArray[np.complex128]
    phases: NDArray[np.float64]
    errors: NDArray[np.float64]


def _carrier_loop(
    symbols: ArrayLike,
    kp: float,
    ki: float,
    phase: float,
    decide: Callable[[float, float], tuple[float, float]],
) -> CarrierRecovery:
    """The decision-directed PI loop shared by the carrier trackers; ``decide`` gives ``d``."""
    z = np.asarray(symbols)
    if z.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    z = np.asarray(z, dtype=np.complex128)
    if not np.all(np.isfinite(z)):
        raise ValueError("symbols must be finite")
    p = real(kp, "kp")
    i = real(ki, "ki")
    phi = real(phase, "phase")
    if p < 0 or i < 0:
        raise ValueError("kp and ki must not be negative")
    out: list[complex] = []
    phases: list[float] = []
    errors: list[float] = []
    v = 0.0
    for x in z.tolist():
        c = math.cos(phi)
        s = math.sin(phi)
        re = x.real * c + x.imag * s
        im = x.imag * c - x.real * s
        dre, dim = decide(re, im)
        e = dre * im - dim * re
        out.append(complex(re, im))
        phases.append(phi)
        errors.append(e)
        v += i * e
        phi = phi + p * e + v
    return CarrierRecovery(
        np.array(out, dtype=np.complex128),
        np.array(phases, dtype=np.float64),
        np.array(errors, dtype=np.float64),
    )


def _qpsk_decision(re: float, im: float) -> tuple[float, float]:
    return (1.0 if re >= 0 else -1.0, 1.0 if im >= 0 else -1.0)


_C8 = 1 / math.sqrt(2)
_PSK8_POINTS = [(1.0, 0.0), (_C8, _C8), (0.0, 1.0), (-_C8, _C8),
                (-1.0, 0.0), (-_C8, -_C8), (0.0, -1.0), (_C8, -_C8)]  # fmt: skip


def _psk8_decision(re: float, im: float) -> tuple[float, float]:
    return _PSK8_POINTS[math.floor(math.atan2(im, re) / (math.pi / 4) + 0.5) % 8]


def _qam16_level(v: float) -> float:
    m = 1.0 if abs(v) < _QAM16_THRESHOLD else 3.0
    return (m if v >= 0 else -m) * _INV_SQRT10


def _qam16_decision(re: float, im: float) -> tuple[float, float]:
    return (_qam16_level(re), _qam16_level(im))


def qpsk_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed QPSK carrier loop: a PI loop on the phase, one update per symbol
    (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _qpsk_decision)


def psk8_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed 8-PSK carrier loop (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _psk8_decision)


def qam16_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed 16-QAM carrier loop (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _qam16_decision)
