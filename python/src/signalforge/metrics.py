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


def qpsk_ber_theory(eb_n0_db: float) -> float:
    """Bit error rate of Gray-coded QPSK in AWGN: ``0.5 * erfc(sqrt(Eb/N0))``."""
    if math.isnan(eb_n0_db):
        raise ValueError("eb_n0_db must not be NaN")
    try:
        eb_n0 = 10 ** (eb_n0_db / 10)
    except OverflowError:  # above about 3080 dB; C# gets infinity here
        eb_n0 = math.inf
    return 0.5 * math.erfc(math.sqrt(eb_n0))
