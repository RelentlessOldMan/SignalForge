"""Error-rate metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass(frozen=True)
class ErrorCount:
    """Errors over a compared span. ``rate`` is ``errors / compared``, NaN if nothing compared."""

    errors: int
    compared: int
    rate: float


def bit_errors(reference: ArrayLike, received: ArrayLike) -> ErrorCount:
    """Count differing bits between two equal-length bit sequences."""
    a = np.asarray(reference)
    b = np.asarray(received)
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("bit sequences must be one-dimensional")
    if a.shape != b.shape:
        raise ValueError(f"length mismatch: {a.shape[0]} reference vs {b.shape[0]} received")
    errors = int(np.count_nonzero(a != b))
    n = int(a.shape[0])
    return ErrorCount(errors, n, errors / n if n else float("nan"))


@dataclass(frozen=True)
class Evm:
    """Error vector magnitude, normalized to the mean power of the reference symbols."""

    rms: float
    rms_percent: float
    rms_db: float
    peak: float
    peak_index: int
    num_symbols: int


def evm(measured: ArrayLike, reference: ArrayLike) -> Evm:
    """RMS and peak EVM of measured symbols against reference symbols; see docs/conventions.md."""
    m = np.asarray(measured, dtype=np.complex128)
    r = np.asarray(reference, dtype=np.complex128)
    if m.ndim != 1 or m.shape != r.shape or m.size == 0:
        raise ValueError("measured and reference must be non-empty 1-D arrays of the same length")
    if not (np.all(np.isfinite(m)) and np.all(np.isfinite(r))):
        raise ValueError("symbols must be finite")
    ref_power = float(np.sum(np.abs(r) ** 2))
    if not ref_power > 0:
        raise ValueError("reference power must be positive")
    e = np.abs(m - r)
    rms = math.sqrt(float(np.sum(e * e)) / ref_power)
    k = int(np.argmax(e))
    return Evm(
        rms=rms,
        rms_percent=100 * rms,
        rms_db=20 * math.log10(rms) if rms > 0 else -math.inf,
        peak=float(e[k]) / math.sqrt(ref_power / m.size),
        peak_index=k,
        num_symbols=int(m.size),
    )


def _eb_n0(eb_n0_db: float) -> float:
    if math.isnan(eb_n0_db):
        raise ValueError("eb_n0_db must not be NaN")
    try:
        return float(10 ** (eb_n0_db / 10))
    except OverflowError:  # above about 3080 dB; C# gets infinity here
        return math.inf


def qpsk_ber_theory(eb_n0_db: float) -> float:
    """Bit error rate of Gray-coded QPSK in AWGN: ``0.5 * erfc(sqrt(Eb/N0))``."""
    return 0.5 * math.erfc(math.sqrt(_eb_n0(eb_n0_db)))


def qpsk_ber_rayleigh_theory(eb_n0_db: float) -> float:
    """Bit error rate of Gray QPSK in Rayleigh fading with a coherent receiver, mean Eb/N0 in dB:
    ``0.5 * (1 - sqrt(g / (1 + g)))`` (conventions: EVM and BER)."""
    g = _eb_n0(eb_n0_db)
    if math.isinf(g):
        return 0.0
    return 1 / (2 * (1 + g) * (1 + math.sqrt(g / (1 + g))))


def qam16_ber_theory(eb_n0_db: float) -> float:
    """Exact bit error rate of Gray 16-QAM in AWGN (conventions: EVM and BER)."""
    r = math.sqrt(2 * _eb_n0(eb_n0_db) / 5)
    return (3 * math.erfc(r) + 2 * math.erfc(3 * r) - math.erfc(5 * r)) / 8


def qam16_ser_theory(eb_n0_db: float) -> float:
    """Exact symbol error rate of 16-QAM in AWGN: ``p*(2 - p)``, ``p = 0.75*erfc(r)``."""
    p = 0.75 * math.erfc(math.sqrt(2 * _eb_n0(eb_n0_db) / 5))
    return p * (2 - p)


_TAIL_PANELS = 4096


def _phase_tail(psi: float, es_n0: float) -> float:
    """P(received phase beyond psi on one side), Pawula's integral by Simpson's rule."""
    k = es_n0 * math.sin(psi) ** 2
    if k == 0:
        return (math.pi - psi) / (2 * math.pi)
    if math.isinf(k):
        return 0.0
    h = (math.pi - psi) / _TAIL_PANELS
    theta = h * np.arange(1, _TAIL_PANELS)
    inner = np.exp(-k / np.sin(theta) ** 2)
    weights = np.where(np.arange(1, _TAIL_PANELS) % 2 == 1, 4.0, 2.0)
    total = float(np.dot(weights, inner)) + math.exp(-es_n0)  # the theta = 0 end is 0
    return total * h / 3 / (2 * math.pi)


def psk8_ser_theory(eb_n0_db: float) -> float:
    """Exact symbol error rate of 8-PSK in AWGN: ``2*T(pi/8)`` (conventions: EVM and BER)."""
    return 2 * _phase_tail(math.pi / 8, 3 * _eb_n0(eb_n0_db))


def psk8_ber_theory(eb_n0_db: float) -> float:
    """Exact bit error rate of Gray 8-PSK in AWGN: ``(2/3)*(T(pi/8) + T(3*pi/8))``."""
    es_n0 = 3 * _eb_n0(eb_n0_db)
    return 2 / 3 * (_phase_tail(math.pi / 8, es_n0) + _phase_tail(3 * math.pi / 8, es_n0))
