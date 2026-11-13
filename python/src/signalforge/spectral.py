"""FFT, frequency axes, windows, Welch PSD, occupied bandwidth and channel power.

Definitions are in docs/conventions.md (Spectra) and docs/adr/0006-fft-windows-spectra.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count, real

_COSINE_SUMS: dict[str, tuple[float, ...]] = {
    "rectangular": (1.0,),
    "hann": (0.5, 0.5),
    "hamming": (0.54, 0.46),
    "blackman": (0.42, 0.5, 0.08),
    "blackman_harris": (0.35875, 0.48829, 0.14128, 0.01168),
    "flattop": (0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368),
}

WINDOWS = (*_COSINE_SUMS, "kaiser")

KAISER_MAX_BETA = 700.0
"""Largest Kaiser beta: I0(beta) overflows a double just above 713."""


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
    if count(n, "n") < 1:
        raise ValueError("n must be at least 1")
    if not 0 < sample_rate < math.inf:
        raise ValueError("sample_rate must be positive and finite")
    i = np.arange(n)
    k = i - n // 2 if shifted else np.where(i <= (n - 1) // 2, i, i - n)
    return np.asarray(k * (sample_rate / n), dtype=np.float64)


def window(
    name: str, n: int, *, symmetric: bool = False, beta: float | None = None
) -> NDArray[np.float64]:
    """A named window of length ``n``; periodic unless ``symmetric``. ``kaiser`` needs ``beta``."""
    n = count(n, "n")
    if name == "kaiser":
        if beta is None or not 0 <= beta <= KAISER_MAX_BETA:
            raise ValueError(f"kaiser needs 0 <= beta <= {KAISER_MAX_BETA:g}")
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
    nfft: int

    @property
    def span(self) -> Span | None:
        """``(0, fs/2)`` for a one-sided PSD (its DC and Nyquist bins are half bins), else None."""
        return (0.0, self.sample_rate / 2) if self.one_sided else None


@dataclass(frozen=True)
class Spectrogram:
    """Welch segments kept one per row, in sample-units²/Hz; see docs/conventions.md (Spectra)."""

    frequencies: NDArray[np.float64]
    times: NDArray[np.float64]
    psd: NDArray[np.float64]
    sample_rate: float
    nperseg: int
    num_segments: int
    one_sided: bool
    bin_width: float
    enbw_hz: float
    nfft: int

    @property
    def span(self) -> Span | None:
        """``(0, fs/2)`` for one-sided rows (their DC and Nyquist bins are half bins), else None."""
        return (0.0, self.sample_rate / 2) if self.one_sided else None


@dataclass(frozen=True)
class _Segments:
    x: NDArray[Any]
    n: int
    step: int
    count: int
    w: NDArray[np.float64]
    scale: float
    one_sided: bool
    detrend: str
    nfft: int

    def power(self, s: int) -> NDArray[np.float64]:
        """``|FFT(w*detrended segment s)|^2``, unscaled, in FFT order."""
        seg = self.x[s * self.step : s * self.step + self.n]
        if self.detrend != "none":
            seg = seg - np.mean(seg)
            if self.detrend == "linear" and self.n > 1:
                t = np.arange(self.n) - (self.n - 1) / 2
                seg = seg - t * (np.sum(t * seg) / np.sum(t * t))
        return np.abs(np.fft.fft(seg * self.w, self.nfft)) ** 2

    def fold(self, p: NDArray[np.float64]) -> NDArray[np.float64]:
        """FFT-order power to the PSD's bins: one-sided (doubled) or shifted."""
        if not self.one_sided:
            return np.fft.fftshift(p)
        m = self.nfft // 2 + 1
        p = p[:m].copy()
        p[1 : m - 1 if self.nfft % 2 == 0 else m] *= 2.0
        return p

    def frequencies(self, sample_rate: float) -> NDArray[np.float64]:
        if self.one_sided:
            return np.arange(self.nfft // 2 + 1, dtype=np.float64) * (sample_rate / self.nfft)
        return np.asarray(fft_frequencies(self.nfft, sample_rate, shifted=True), dtype=np.float64)


def _segments(
    samples: ArrayLike,
    sample_rate: float,
    nperseg: int | None,
    noverlap: int | None,
    window: str,
    one_sided: bool | None,
    beta: float | None,
    detrend: str,
    nfft: int | None,
) -> _Segments:
    x = _vector(samples, "samples")
    if detrend not in ("none", "constant", "linear"):
        raise ValueError('detrend must be "none", "constant" or "linear"')
    if not real(sample_rate, "sample_rate") > 0:
        raise ValueError("sample_rate must be positive and finite")
    is_complex = np.iscomplexobj(x)
    if one_sided is None:
        one_sided = not is_complex
    elif one_sided and is_complex:
        raise ValueError("a one-sided PSD needs real samples")
    n = x.size if nperseg is None else count(nperseg, "nperseg")
    if n < 1:
        raise ValueError("nperseg must be at least 1")
    if x.size < n:
        raise ValueError("fewer samples than nperseg")
    overlap = n // 2 if noverlap is None else count(noverlap, "noverlap")
    if not overlap < n:
        raise ValueError("noverlap must satisfy 0 <= noverlap < nperseg")
    step = n - overlap
    m = n if nfft is None else count(nfft, "nfft")
    if m < n:
        raise ValueError("nfft must be at least nperseg")
    w = _window_for_psd(window, n, beta)
    scale = 1.0 / (sample_rate * float(np.sum(w * w)))
    return _Segments(x, n, step, (x.size - n) // step + 1, w, scale, bool(one_sided), detrend, m)


def welch_psd(
    samples: ArrayLike,
    sample_rate: float,
    *,
    nperseg: int | None = None,
    noverlap: int | None = None,
    window: str = "hann",
    one_sided: bool | None = None,
    beta: float | None = None,
    detrend: str = "none",
    average: str = "mean",
    nfft: int | None = None,
) -> SpectralDensity:
    """Welch PSD: mean (or bias-corrected median) of ``|FFT(w*segment)|^2 / (fs*sum(w^2))`` over
    overlapping, optionally detrended and zero-padded segments."""
    g = _segments(samples, sample_rate, nperseg, noverlap, window, one_sided, beta, detrend, nfft)
    if average == "mean":
        acc = np.zeros(g.nfft)
        for s in range(g.count):
            acc += g.power(s)
        two_sided = acc * (g.scale / g.count)
    elif average == "median":
        rows = np.array([g.power(s) for s in range(g.count)])
        two_sided = np.median(rows, axis=0) * (g.scale / _median_bias(g.count))
    else:
        raise ValueError('average must be "mean" or "median"')
    return SpectralDensity(
        frequencies=g.frequencies(sample_rate),
        psd=np.asarray(g.fold(two_sided), dtype=np.float64),
        sample_rate=float(sample_rate),
        nperseg=g.n,
        num_segments=g.count,
        one_sided=g.one_sided,
        bin_width=sample_rate / g.nfft,
        enbw_hz=window_stats(g.w).enbw_bins * sample_rate / g.n,
        nfft=g.nfft,
    )


def spectrogram(
    samples: ArrayLike,
    sample_rate: float,
    nperseg: int,
    *,
    noverlap: int | None = None,
    window: str = "hann",
    one_sided: bool | None = None,
    beta: float | None = None,
    detrend: str = "none",
    nfft: int | None = None,
) -> Spectrogram:
    """Welch's segments kept, not averaged: row ``s`` is the PSD of segment ``s`` alone."""
    if nperseg is None:
        raise ValueError("nperseg is required")
    g = _segments(samples, sample_rate, nperseg, noverlap, window, one_sided, beta, detrend, nfft)
    rows = [g.fold(g.power(s) * g.scale) for s in range(g.count)]
    return Spectrogram(
        frequencies=g.frequencies(sample_rate),
        times=(np.arange(g.count, dtype=np.float64) * g.step + g.n / 2) / sample_rate,
        psd=np.asarray(rows, dtype=np.float64),
        sample_rate=float(sample_rate),
        nperseg=g.n,
        num_segments=g.count,
        one_sided=g.one_sided,
        bin_width=sample_rate / g.nfft,
        enbw_hz=window_stats(g.w).enbw_bins * sample_rate / g.n,
        nfft=g.nfft,
    )


def _median_bias(k: int) -> float:
    """The expected median of ``k`` independent unit-mean exponential values (conventions: PSD)."""
    m = k // 2
    b = math.fsum(1.0 / i for i in range(m + 1, k + 1))
    return b + 1.0 / k if k % 2 == 0 else b


def _window_for_psd(name: str, n: int, beta: float | None) -> NDArray[np.float64]:
    w = window(name, n, beta=beta)
    if not np.any(w):
        raise ValueError(f"{name} window of length {n} is all zeros")
    return w


Span = tuple[float, float]


def _bins(
    frequencies: ArrayLike, psd: ArrayLike, span: Span | ArrayLike | None
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Validated bin powers ``psd*delta`` and bin edges ``left``, ``right``, clipped to span."""
    f = np.asarray(frequencies, dtype=np.float64)
    p = np.asarray(psd, dtype=np.float64)
    if f.ndim != 1 or p.shape != f.shape:
        raise ValueError("frequencies and psd must be 1-D arrays of the same length")
    if f.size < 2:
        raise ValueError("need at least two bins")
    if not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be finite")
    if not (np.all(np.isfinite(p)) and np.all(p >= 0)):
        raise ValueError("psd must be finite and non-negative")
    with np.errstate(over="ignore", invalid="ignore"):
        delta = float(f[-1] - f[0]) / (f.size - 1)
        even = np.all(np.abs(np.diff(f) - delta) <= 1e-6 * delta)  # NaN fails
    if not (math.isfinite(delta) and delta > 0 and even):
        raise ValueError("frequencies must be ascending, evenly spaced, with a finite spacing")
    left, right = f - delta / 2, f + delta / 2
    if span is not None:
        s = np.asarray(span, dtype=np.float64)
        if s.shape != (2,) or not (s[0] <= f[0] and s[1] >= f[-1]):
            raise ValueError(
                "span must be (low, high) with low <= the first and high >= the last bin"
            )
        left, right = np.maximum(left, s[0]), np.minimum(right, s[1])
    if not np.all(right > left):
        raise ValueError("half a bin rounds to nothing at these frequencies")
    with np.errstate(over="ignore"):
        power = p * delta
        total = float(np.sum(power))
    if not math.isfinite(total):
        raise ValueError("psd too large: the bin powers or their sum overflow")
    return power, left, right


@dataclass(frozen=True)
class OccupiedBandwidth:
    """Occupied bandwidth by the β/2 method; frequencies in the PSD's axis."""

    bandwidth: float
    lower: float
    upper: float
    total_power: float
    fraction: float


def occupied_bandwidth(
    frequencies: ArrayLike,
    psd: ArrayLike,
    fraction: float = 0.99,
    *,
    span: Span | ArrayLike | None = None,
) -> OccupiedBandwidth:
    """Band holding ``fraction`` of the power, with ``(1-fraction)/2`` left out on each side.

    ``span`` clips the outer bins (a one-sided PSD: ``SpectralDensity.span``, ``(0, fs/2)``).
    """
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    power, left, right = _bins(frequencies, psd, span)
    cum = np.concatenate(([0.0], np.cumsum(power)))  # cum[k] = power before bin k
    total = float(cum[-1])
    if not total > 0:
        raise ValueError("total power must be positive")
    lo_target = (1 - fraction) / 2 * total
    hi_target = (1 + fraction) / 2 * total
    k_lo = int(np.argmax(cum[1:] > lo_target))
    lower = float(left[k_lo] + (lo_target - cum[k_lo]) / power[k_lo] * (right[k_lo] - left[k_lo]))
    k_hi = int(np.nonzero(cum[:-1] < hi_target)[0][-1])
    upper = float(left[k_hi] + (hi_target - cum[k_hi]) / power[k_hi] * (right[k_hi] - left[k_hi]))
    return OccupiedBandwidth(
        bandwidth=upper - lower, lower=lower, upper=upper, total_power=total, fraction=fraction
    )


@dataclass(frozen=True)
class Acpr:
    """Adjacent channel power ratio: power in each adjacent channel relative to the main one
    (conventions: Spectra, ACPR)."""

    main_power: float
    lower_power: NDArray[np.float64]
    upper_power: NDArray[np.float64]
    lower_dbc: NDArray[np.float64]
    upper_dbc: NDArray[np.float64]


def acpr(
    frequencies: ArrayLike,
    psd: ArrayLike,
    center: float,
    bandwidth: float,
    offsets: ArrayLike,
    *,
    adjacent_bandwidth: float | None = None,
    span: Span | ArrayLike | None = None,
) -> Acpr:
    """Power in the main channel and in the lower and upper channels at each center-to-center
    offset, by the channel power rule; every channel must lie inside the spectrum."""
    c = real(center, "center")
    b = real(bandwidth, "bandwidth")
    ba = b if adjacent_bandwidth is None else real(adjacent_bandwidth, "adjacent_bandwidth")
    if not (b > 0 and ba > 0):
        raise ValueError("bandwidth and adjacent_bandwidth must be positive")
    o = np.asarray(offsets, dtype=np.float64)
    if o.ndim != 1 or o.size == 0 or not np.all(np.isfinite(o) & (o > 0)):
        raise ValueError("offsets must be a non-empty list of finite values > 0")
    power, left, right = _bins(frequencies, psd, span)
    slack = 1e-9 * float(np.max(right - left))  # rounding in center +- offset +- width/2

    def channel(low: float, high: float) -> float:
        if low < left[0] - slack or high > right[-1] + slack:
            raise ValueError(
                f"channel [{low}, {high}] leaves the spectrum [{left[0]}, {right[-1]}]"
            )
        overlap = np.clip(np.minimum(right, high) - np.maximum(left, low), 0.0, None)
        return float(np.sum(power * overlap / (right - left)))

    main = channel(c - b / 2, c + b / 2)
    if not main > 0:
        raise ValueError("the main channel has no power")
    lower = np.array([channel(c - v - ba / 2, c - v + ba / 2) for v in o])
    upper = np.array([channel(c + v - ba / 2, c + v + ba / 2) for v in o])
    with np.errstate(divide="ignore"):
        db_main = math.log10(main)  # a difference of logs: the ratio itself could underflow
        return Acpr(
            main, lower, upper, 10 * (np.log10(lower) - db_main), 10 * (np.log10(upper) - db_main)
        )


def channel_power(
    frequencies: ArrayLike,
    psd: ArrayLike,
    low: float,
    high: float,
    *,
    span: Span | ArrayLike | None = None,
) -> float:
    """PSD integrated over ``[low, high]``; bins count by the part of their width inside.

    ``span`` clips the outer bins, as for ``occupied_bandwidth``.
    """
    lo, hi = real(low, "low"), real(high, "high")
    if not lo < hi:
        raise ValueError("need finite low < high")
    power, left, right = _bins(frequencies, psd, span)
    overlap = np.clip(np.minimum(right, hi) - np.maximum(left, lo), 0.0, None)
    return float(np.sum(power * overlap / (right - left)))
