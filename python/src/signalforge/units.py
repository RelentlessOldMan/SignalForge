"""Unit conversions: dB, dBm, voltage and power. Definitions in docs/conventions.md."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

#: Default reference impedance in ohms.
DEFAULT_IMPEDANCE = 50.0


def _non_negative(x: ArrayLike, what: str) -> NDArray[np.float64]:
    a = np.asarray(x, dtype=np.float64)
    if np.any(np.isnan(a)) or np.any(a < 0):
        raise ValueError(f"{what} must be non-negative")
    return a


def _positive(value: float, what: str) -> float:
    if not 0 < value < math.inf:
        raise ValueError(f"{what} must be positive and finite")
    return float(value)


def _out(a: NDArray[np.float64]) -> NDArray[np.float64] | float:
    return float(a) if a.ndim == 0 else a


def _log10(a: NDArray[np.float64]) -> NDArray[np.float64]:
    with np.errstate(divide="ignore"):
        return np.log10(a)


def lin_to_db(ratio: ArrayLike) -> NDArray[np.float64] | float:
    """Power ratio to dB: ``10*log10(ratio)``. Zero gives -inf; negative raises ``ValueError``."""
    return _out(10.0 * _log10(_non_negative(ratio, "power ratio")))


def db_to_lin(db: ArrayLike) -> NDArray[np.float64] | float:
    """dB to power ratio: ``10**(db/10)``."""
    return _out(np.power(10.0, np.asarray(db, dtype=np.float64) / 10.0))


def amp_to_db(ratio: ArrayLike) -> NDArray[np.float64] | float:
    """Amplitude ratio to dB: ``20*log10(ratio)``. Zero gives -inf; negative raises ValueError."""
    return _out(20.0 * _log10(_non_negative(ratio, "amplitude ratio")))


def db_to_amp(db: ArrayLike) -> NDArray[np.float64] | float:
    """dB to amplitude ratio: ``10**(db/20)``."""
    return _out(np.power(10.0, np.asarray(db, dtype=np.float64) / 20.0))


def w_to_dbm(watts: ArrayLike) -> NDArray[np.float64] | float:
    """Power in watts to dBm."""
    return _out(10.0 * _log10(_non_negative(watts, "power") / 1e-3))


def dbm_to_w(dbm: ArrayLike) -> NDArray[np.float64] | float:
    """Power in dBm to watts."""
    return _out(1e-3 * np.power(10.0, np.asarray(dbm, dtype=np.float64) / 10.0))


def vrms_to_dbm(
    vrms: ArrayLike, impedance: float = DEFAULT_IMPEDANCE
) -> NDArray[np.float64] | float:
    """RMS voltage across ``impedance`` ohms to dBm (``P = Vrms**2 / R``)."""
    r = _positive(impedance, "impedance")
    v = _non_negative(vrms, "RMS voltage")
    return _out(10.0 * _log10(v * v / r / 1e-3))


def dbm_to_vrms(
    dbm: ArrayLike, impedance: float = DEFAULT_IMPEDANCE
) -> NDArray[np.float64] | float:
    """Power in dBm to RMS voltage across ``impedance`` ohms."""
    r = _positive(impedance, "impedance")
    p = 1e-3 * np.power(10.0, np.asarray(dbm, dtype=np.float64) / 10.0)
    return _out(np.sqrt(p * r))
