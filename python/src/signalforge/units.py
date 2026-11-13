"""Unit conversions: dB, dBm, voltage and power. Definitions in docs/conventions.md."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

#: Default reference impedance in ohms.
DEFAULT_IMPEDANCE = 50.0


def _non_negative(x: ArrayLike, what: str) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64)
    if np.any(np.isnan(a)) or np.any(a < 0):
        raise ValueError(f"{what} must be non-negative")
    return a


def _positive(value: float, what: str) -> float:
    if not value > 0:
        raise ValueError(f"{what} must be positive")
    return float(value)


def _out(a: np.ndarray) -> np.ndarray | float:
    return float(a) if a.ndim == 0 else a


def _log10(a: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore"):
        return np.log10(a)


def lin_to_db(ratio: ArrayLike) -> np.ndarray | float:
    """Power ratio to dB: ``10*log10(ratio)``. Zero gives -inf; negative raises ``ValueError``."""
    return _out(10.0 * _log10(_non_negative(ratio, "power ratio")))


def db_to_lin(db: ArrayLike) -> np.ndarray | float:
    """dB to power ratio: ``10**(db/10)``."""
    return _out(np.power(10.0, np.asarray(db, dtype=np.float64) / 10.0))


def amp_to_db(ratio: ArrayLike) -> np.ndarray | float:
    """Amplitude ratio to dB: ``20*log10(ratio)``. Zero gives -inf; negative raises ValueError."""
    return _out(20.0 * _log10(_non_negative(ratio, "amplitude ratio")))


def db_to_amp(db: ArrayLike) -> np.ndarray | float:
    """dB to amplitude ratio: ``10**(db/20)``."""
    return _out(np.power(10.0, np.asarray(db, dtype=np.float64) / 20.0))


def w_to_dbm(watts: ArrayLike) -> np.ndarray | float:
    """Power in watts to dBm."""
    return _out(10.0 * _log10(_non_negative(watts, "power") / 1e-3))


def dbm_to_w(dbm: ArrayLike) -> np.ndarray | float:
    """Power in dBm to watts."""
    return _out(1e-3 * np.power(10.0, np.asarray(dbm, dtype=np.float64) / 10.0))


def vrms_to_dbm(vrms: ArrayLike, impedance: float = DEFAULT_IMPEDANCE) -> np.ndarray | float:
    """RMS voltage across ``impedance`` ohms to dBm (``P = Vrms**2 / R``)."""
    r = _positive(impedance, "impedance")
    v = _non_negative(vrms, "RMS voltage")
    return _out(10.0 * _log10(v * v / r / 1e-3))


def dbm_to_vrms(dbm: ArrayLike, impedance: float = DEFAULT_IMPEDANCE) -> np.ndarray | float:
    """Power in dBm to RMS voltage across ``impedance`` ohms."""
    r = _positive(impedance, "impedance")
    p = 1e-3 * np.power(10.0, np.asarray(dbm, dtype=np.float64) / 10.0)
    return _out(np.sqrt(p * r))
