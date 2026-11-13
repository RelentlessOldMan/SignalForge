"""FFT, frequency axes, windows, Welch PSD, occupied bandwidth and channel power.

Definitions are in docs/conventions.md (Spectra) and docs/adr/0006-fft-windows-spectra.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

_COSINE_SUMS: dict[str, tuple[float, ...]] = {
    "rectangular": (1.0,),
    "hann": (0.5, 0.5),
    "hamming": (0.54, 0.46),
    "blackman": (0.42, 0.5, 0.08),
    "blackman_harris": (0.35875, 0.48829, 0.14128, 0.01168),
    "flattop": (0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368),
}

WINDOWS = (*_COSINE_SUMS, "kaiser")


def _vector(x: ArrayLike, what: str) -> NDArray[np.complex128] | NDArray[np.float64]:
    a = np.asarray(x)
    if a.ndim != 1:
        raise ValueError(f"{what} must be one-dimensional")
    if np.iscomplexobj(a):
        return np.asarray(a, dtype=np.complex128)
    return np.asarray(a, dtype=np.float64)


def fft(samples: ArrayLike) -> NDArray[np.complex128]:
    """Forward DFT, unnormalized: ``X[k] = sum x[n] exp(-2j*pi*k*n/N)``. Needs ``N >= 1``."""
    x = _vector(samples, "samples")
    if x.size == 0:
        raise ValueError("fft needs at least one sample")
    return np.asarray(np.fft.fft(x), dtype=np.complex128)


def ifft(spectrum: ArrayLike) -> NDArray[np.complex128]:
    """Inverse DFT, scaled by ``1/N``. Needs ``N >= 1``."""
    x = _vector(spectrum, "spectrum")
    if x.size == 0:
        raise ValueError("ifft needs at least one bin")
    return np.asarray(np.fft.ifft(x), dtype=np.complex128)


def fft_frequencies(n: int, sample_rate: float, shifted: bool = False) -> NDArray[np.float64]:
    """Bin frequencies of an ``n``-point FFT: NumPy ``fftfreq`` order, or ``fftshift`` order."""
    if n < 1:
        raise ValueError("n must be at least 1")
    if not sample_rate > 0:
        raise ValueError("sample_rate must be positive")
    i = np.arange(n)
    k = i - n // 2 if shifted else np.where(i <= (n - 1) // 2, i, i - n)
    return np.asarray(k * (sample_rate / n), dtype=np.float64)


def window(
    name: str, n: int, *, symmetric: bool = False, beta: float | None = None
) -> NDArray[np.float64]:
    """A named window of length ``n``; periodic unless ``symmetric``. ``kaiser`` needs ``beta``."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if name == "kaiser":
        if beta is None or not beta >= 0:
            raise ValueError("kaiser needs beta >= 0")
    elif name not in _COSINE_SUMS:
        raise ValueError(f"unknown window {name!r}; known: {', '.join(WINDOWS)}")
    elif beta is not None:
        raise ValueError("beta applies to the kaiser window only")
    if n == 0:
        return np.zeros(0)
    if n == 1:
        return np.ones(1)
    d = n - 1 if symmetric else n
    i = np.arange(n, dtype=np.float64)
    if name == "kaiser":
        assert beta is not None
        r = 2.0 * i / d - 1.0
        return np.asarray(np.i0(beta * np.sqrt(np.clip(1.0 - r * r, 0.0, None))) / np.i0(beta))
    w = np.zeros(n)
    for k, a in enumerate(_COSINE_SUMS[name]):
        w += (-1) ** k * a * np.cos(2.0 * np.pi * k * i / d)
    return w


@dataclass(frozen=True)
class WindowStats:
    """Coherent gain ``sum(w)/N`` and equivalent noise bandwidth in bins ``N*sum(w^2)/sum(w)^2``."""

    coherent_gain: float
    enbw_bins: float


def window_stats(w: ArrayLike) -> WindowStats:
    """Coherent gain and ENBW (in bins) of a window. The window must not sum to zero."""
    a = np.asarray(w, dtype=np.float64)
    if a.ndim != 1 or a.size == 0:
        raise ValueError("window must be a non-empty 1-D array")
    s = float(np.sum(a))
    if s == 0:
        raise ValueError("window sums to zero")
    n = a.size
    return WindowStats(coherent_gain=s / n, enbw_bins=n * float(np.sum(a * a)) / (s * s))


@dataclass(frozen=True)
class SpectralDensity:
    """A power spectral density in sample-units²/Hz; see docs/conventions.md (Spectra)."""

    frequencies: NDArray[np.float64]
    psd: NDArray[np.float64]
    sample_rate: float
    nperseg: int
    num_segments: int
    one_sided: bool
    bin_width: float
    enbw_hz: float


def welch_psd(
    samples: ArrayLike,
    sample_rate: float,
    *,
    nperseg: int | None = None,
    noverlap: int | None = None,
    window: str = "hann",
    one_sided: bool | None = None,
) -> SpectralDensity:
    """Welch PSD: mean of ``|FFT(w*segment)|^2 / (fs*sum(w^2))`` over overlapping segments."""
    x = _vector(samples, "samples")
    if not sample_rate > 0:
        raise ValueError("sample_rate must be positive")
    is_complex = np.iscomplexobj(x)
    if one_sided is None:
        one_sided = not is_complex
    elif one_sided and is_complex:
        raise ValueError("a one-sided PSD needs real samples")
    n = x.size if nperseg is None else nperseg
    if n < 1:
        raise ValueError("nperseg must be at least 1")
    if x.size < n:
        raise ValueError("fewer samples than nperseg")
    overlap = n // 2 if noverlap is None else noverlap
    if not 0 <= overlap < n:
        raise ValueError("noverlap must satisfy 0 <= noverlap < nperseg")
    step = n - overlap
    num_segments = (x.size - n) // step + 1
    w = _window_for_psd(window, n)
    scale = 1.0 / (sample_rate * float(np.sum(w * w)))
    acc = np.zeros(n)
    for s in range(num_segments):
        seg = x[s * step : s * step + n]
        acc += np.abs(np.fft.fft(seg * w)) ** 2
    p = acc * (scale / num_segments)
    if one_sided:
        m = n // 2 + 1
        p = p[:m].copy()
        last = m - 1 if n % 2 == 0 else m
        p[1:last] *= 2.0
        freqs = np.arange(m) * (sample_rate / n)
    else:
        p = np.fft.fftshift(p)
        freqs = fft_frequencies(n, sample_rate, shifted=True)
    stats = window_stats(w)
    return SpectralDensity(
        frequencies=np.asarray(freqs, dtype=np.float64),
        psd=np.asarray(p, dtype=np.float64),
        sample_rate=float(sample_rate),
        nperseg=n,
        num_segments=num_segments,
        one_sided=bool(one_sided),
        bin_width=sample_rate / n,
        enbw_hz=stats.enbw_bins * sample_rate / n,
    )


def _window_for_psd(name: str, n: int) -> NDArray[np.float64]:
    w = window(name, n)
    if not np.any(w):
        raise ValueError(f"{name} window of length {n} is all zeros")
    return w


def _bins(frequencies: ArrayLike, psd: ArrayLike) -> tuple[NDArray[np.float64], float]:
    """Validated bin powers ``psd*delta`` and the bin spacing ``delta``."""
    f = np.asarray(frequencies, dtype=np.float64)
    p = np.asarray(psd, dtype=np.float64)
    if f.ndim != 1 or p.shape != f.shape:
        raise ValueError("frequencies and psd must be 1-D arrays of the same length")
    if f.size < 2:
        raise ValueError("need at least two bins")
    if not (np.all(np.isfinite(p)) and np.all(p >= 0)):
        raise ValueError("psd must be finite and non-negative")
    delta = float(f[-1] - f[0]) / (f.size - 1)
    if not delta > 0 or np.any(np.abs(np.diff(f) - delta) > 1e-6 * delta):
        raise ValueError("frequencies must be ascending and evenly spaced")
    return p * delta, delta


@dataclass(frozen=True)
class OccupiedBandwidth:
    """Occupied bandwidth by the β/2 method; frequencies in the PSD's axis."""

    bandwidth: float
    lower: float
    upper: float
    total_power: float
    fraction: float


def occupied_bandwidth(
    frequencies: ArrayLike, psd: ArrayLike, fraction: float = 0.99
) -> OccupiedBandwidth:
    """Band holding ``fraction`` of the power, with ``(1-fraction)/2`` left out on each side."""
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    power, delta = _bins(frequencies, psd)
    f = np.asarray(frequencies, dtype=np.float64)
    edges = f - delta / 2
    total = float(np.sum(power))
    if not total > 0:
        raise ValueError("total power must be positive")
    cum = np.concatenate(([0.0], np.cumsum(power)))  # cum[k] = power before bin k
    lo_target = (1 - fraction) / 2 * total
    hi_target = (1 + fraction) / 2 * total
    k_lo = int(np.argmax(cum[1:] > lo_target))
    lower = float(edges[k_lo] + (lo_target - cum[k_lo]) / power[k_lo] * delta)
    k_hi = int(np.nonzero(cum[:-1] < hi_target)[0][-1])
    upper = float(edges[k_hi] + (hi_target - cum[k_hi]) / power[k_hi] * delta)
    return OccupiedBandwidth(
        bandwidth=upper - lower, lower=lower, upper=upper, total_power=total, fraction=fraction
    )


def channel_power(frequencies: ArrayLike, psd: ArrayLike, low: float, high: float) -> float:
    """PSD integrated over ``[low, high]``; bins count by the part of their width inside."""
    if not (math.isfinite(low) and math.isfinite(high) and low < high):
        raise ValueError("need finite low < high")
    power, delta = _bins(frequencies, psd)
    f = np.asarray(frequencies, dtype=np.float64)
    left = f - delta / 2
    overlap = np.clip(np.minimum(left + delta, high) - np.maximum(left, low), 0.0, None)
    return float(np.sum(power * overlap / delta))
