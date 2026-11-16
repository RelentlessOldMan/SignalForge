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


def _mel_scale(scale: str) -> str:
    if scale not in ("htk", "slaney"):
        raise ValueError('scale must be "htk" or "slaney"')
    return scale


def _finite_non_negative(x: ArrayLike, what: str) -> NDArray[np.float64]:
    a = np.asarray(x, dtype=np.float64)
    if not np.all(np.isfinite(a)) or np.any(a < 0):
        raise ValueError(f"{what} must be finite and non-negative")
    return a


_SLANEY_HZ_PER_MEL = 200.0 / 3.0
_SLANEY_LOG_STEP = math.log(6.4) / 27.0


def hz_to_mel(hz: ArrayLike, *, scale: str = "htk") -> NDArray[np.float64] | float:
    """Frequency in Hz to mel: HTK ``2595*log10(1 + f/700)``, or Slaney, linear below 1 kHz and
    logarithmic above (conventions: Mel scale; ADR 0154)."""
    kind = _mel_scale(scale)
    f = _finite_non_negative(hz, "hz")
    if kind == "htk":
        return _out(2595.0 * np.log10(1.0 + f / 700.0))
    linear = f / _SLANEY_HZ_PER_MEL
    with np.errstate(divide="ignore"):
        logarithmic = 15.0 + np.log(f / 1000.0) / _SLANEY_LOG_STEP
    return _out(np.where(f >= 1000.0, logarithmic, linear))


def mel_to_hz(mel: ArrayLike, *, scale: str = "htk") -> NDArray[np.float64] | float:
    """Mel to frequency in Hz, the inverse of ``hz_to_mel`` (conventions: Mel scale; ADR 0154)."""
    kind = _mel_scale(scale)
    m = _finite_non_negative(mel, "mel")
    if kind == "htk":
        return _out(700.0 * (np.power(10.0, m / 2595.0) - 1.0))
    linear = m * _SLANEY_HZ_PER_MEL
    logarithmic = 1000.0 * np.exp((m - 15.0) * _SLANEY_LOG_STEP)
    return _out(np.where(m >= 15.0, logarithmic, linear))


def hz_to_erb_rate(hz: ArrayLike) -> NDArray[np.float64] | float:
    """Frequency in Hz to ERB number, ``21.4*log10(4.37 f/1000 + 1)`` (conventions: ERB scale;
    ADR 0160)."""
    f = _finite_non_negative(hz, "hz")
    return _out(21.4 * np.log10(4.37 * f / 1000.0 + 1.0))


def erb_rate_to_hz(erb: ArrayLike) -> NDArray[np.float64] | float:
    """ERB number to frequency in Hz, the inverse of ``hz_to_erb_rate`` (conventions: ERB scale;
    ADR 0160)."""
    e = _finite_non_negative(erb, "erb")
    return _out((np.power(10.0, e / 21.4) - 1.0) * 1000.0 / 4.37)


def erb_bandwidth(hz: ArrayLike) -> NDArray[np.float64] | float:
    """The auditory filter's equivalent rectangular bandwidth in Hz, ``24.7 (4.37 f/1000 + 1)``
    (conventions: ERB scale; ADR 0160)."""
    f = _finite_non_negative(hz, "hz")
    return _out(24.7 * (4.37 * f / 1000.0 + 1.0))
