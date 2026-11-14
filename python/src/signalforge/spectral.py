"""FFT, frequency axes, windows, Welch PSD, Lomb-Scargle, occupied bandwidth and channel power.

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


@dataclass(frozen=True)
class TaperSet:
    """DPSS (Slepian) tapers, one per row, and the fraction of each one's energy in ``[-W, W]``;
    see docs/conventions.md (Spectra, DPSS tapers)."""

    tapers: NDArray[np.float64]
    concentrations: NDArray[np.float64]


def dpss_tapers(length: int, half_bandwidth: float, num_tapers: int | None = None) -> TaperSet:
    """The ``num_tapers`` discrete prolate spheroidal sequences of ``length`` samples most
    concentrated in ``[-W, W]``, ``W = half_bandwidth/length`` (conventions: Spectra, DPSS tapers;
    ADR 0078)."""
    n = count(length, "length")
    if n < 1:
        raise ValueError("length must be at least 1")
    nw, k = _taper_args(n, half_bandwidth, num_tapers)
    tapers = _dpss(n, nw / n, k)
    lag = np.arange(1, n)
    sinc = np.sin(2 * math.pi * (nw / n) * lag) / (math.pi * lag)
    conc = [
        2 * (nw / n) * r[0] + 2 * float(np.dot(sinc, r[1:]))
        for r in (np.correlate(v, v, "full")[n - 1 :] for v in tapers)
    ]
    return TaperSet(tapers, np.array(conc, dtype=np.float64))


def _dpss(n: int, w: float, k: int) -> NDArray[np.float64]:
    cw = math.cos(2 * math.pi * w)
    d = [((n - 1) / 2 - i) ** 2 * cw for i in range(n)]
    e = [0.0] + [i * (n - i) / 2 for i in range(1, n)]  # e[i] couples i - 1 and i
    rows: list[list[float]] = []
    for j in range(k):
        theta = _tridiagonal_eigenvalue(d, e, n - 1 - j)
        rows.append(_inverse_iteration(d, e, theta, j, rows))
    return np.array(rows, dtype=np.float64).reshape(k, n)


def _taper_args(n: int, half_bandwidth: float, num_tapers: int | None) -> tuple[float, int]:
    nw = real(half_bandwidth, "half_bandwidth")
    if not 0 < nw < n / 2:
        raise ValueError("half_bandwidth must be above 0 and below length/2")
    k = max(1, math.floor(2 * nw) - 1) if num_tapers is None else count(num_tapers, "num_tapers")
    if not 1 <= k <= n:
        raise ValueError("num_tapers must be between 1 and length")
    return nw, k


def _sturm(d: list[float], e: list[float], x: float) -> int:
    """How many eigenvalues of the tridiagonal matrix are below ``x``."""
    below = 0
    q = 1.0
    tiny = 1e-300
    for i in range(len(d)):
        q = d[i] - x - (e[i] * e[i] / q if i else 0.0)
        if q == 0.0:
            q = -tiny
        if q < 0:
            below += 1
    return below


def _tridiagonal_eigenvalue(d: list[float], e: list[float], index: int) -> float:
    """The ``index``-th smallest eigenvalue (from 0), by bisection on the Sturm count."""
    lo = min(d[i] - abs(e[i]) - (abs(e[i + 1]) if i + 1 < len(d) else 0.0) for i in range(len(d)))
    hi = max(d[i] + abs(e[i]) + (abs(e[i + 1]) if i + 1 < len(d) else 0.0) for i in range(len(d)))
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid in (lo, hi):
            break
        if _sturm(d, e, mid) > index:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def _inverse_iteration(
    d: list[float], e: list[float], theta: float, k: int, earlier: list[list[float]]
) -> list[float]:
    """The unit eigenvector for ``theta``, with the sign rule for taper ``k``."""
    n = len(d)
    mid = (n - 1) / 2
    v = [1.0 if k % 2 == 0 else mid - i for i in range(n)]
    scale = max(max(abs(x) for x in d), max(abs(x) for x in e), 1.0)
    for _ in range(4):
        v = _shifted_solve(d, e, theta, v, scale)
        for u in earlier:  # against rounding drift toward a neighbor
            dot = sum(a * b for a, b in zip(u, v, strict=True))
            v = [a - dot * b for a, b in zip(v, u, strict=True)]
        norm = math.sqrt(sum(x * x for x in v))
        v = [x / norm for x in v]
    sign = sum(v) if k % 2 == 0 else sum((mid - i) * x for i, x in enumerate(v))
    return [-x for x in v] if sign < 0 else v


def _shifted_solve(
    d: list[float], e: list[float], theta: float, b: list[float], scale: float
) -> list[float]:
    """``(T - theta I) x = b`` by Gaussian elimination with partial pivoting (as LAPACK's gttrf);
    a zero pivot is replaced by a tiny one, as inverse iteration wants."""
    n = len(d)
    eps = 2.0**-52 * scale
    dd = [d[i] - theta for i in range(n)]
    du = [e[i + 1] for i in range(n - 1)] + [0.0]  # row i, column i + 1
    dl = [e[i + 1] for i in range(n - 1)]  # row i + 1, column i
    du2 = [0.0] * n  # row i, column i + 2, after a swap
    y = list(b)
    for i in range(n - 1):
        if abs(dd[i]) >= abs(dl[i]):
            if dd[i] == 0.0:
                dd[i] = eps
            f = dl[i] / dd[i]
            dd[i + 1] -= f * du[i]
            y[i + 1] -= f * y[i]
        else:
            f = dd[i] / dl[i]
            dd[i] = dl[i]
            t = du[i]
            du[i] = dd[i + 1]
            dd[i + 1] = t - f * dd[i + 1]
            du2[i] = du[i + 1]
            du[i + 1] = -f * du[i + 1]
            y[i], y[i + 1] = y[i + 1], y[i] - f * y[i + 1]
    if dd[n - 1] == 0.0:
        dd[n - 1] = eps
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = y[i]
        if i + 1 < n:
            s -= du[i] * x[i + 1]
        if i + 2 < n:
            s -= du2[i] * x[i + 2]
        x[i] = s / dd[i]
    return x


def multitaper_psd(
    samples: ArrayLike,
    sample_rate: float,
    half_bandwidth: float,
    *,
    num_tapers: int | None = None,
    one_sided: bool | None = None,
    nfft: int | None = None,
) -> SpectralDensity:
    """Thomson's multitaper PSD: the mean of the periodograms of the whole input under the DPSS
    tapers, in the Welch scaling (conventions: Spectra, Multitaper PSD; ADR 0078)."""
    x = _vector(samples, "samples")
    if not real(sample_rate, "sample_rate") > 0:
        raise ValueError("sample_rate must be positive and finite")
    is_complex = np.iscomplexobj(x)
    if one_sided is None:
        one_sided = not is_complex
    elif one_sided and is_complex:
        raise ValueError("a one-sided PSD needs real samples")
    n = x.size
    if n < 1:
        raise ValueError("samples needs at least 1")
    m = n if nfft is None else count(nfft, "nfft")
    if m < n:
        raise ValueError("nfft must be at least the input length")
    nw, k = _taper_args(n, half_bandwidth, num_tapers)
    tapers = _dpss(n, nw / n, k)
    acc = np.zeros(m)
    for v in tapers:
        acc += np.abs(np.fft.fft(v * x, m)) ** 2
    g = _Segments(x, n, n, 1, tapers[0], 1.0, bool(one_sided), "none", m)
    return SpectralDensity(
        frequencies=g.frequencies(sample_rate),
        psd=np.asarray(g.fold(acc / (k * sample_rate)), dtype=np.float64),
        sample_rate=float(sample_rate),
        nperseg=n,
        num_segments=k,
        one_sided=bool(one_sided),
        bin_width=sample_rate / m,
        enbw_hz=2 * nw / n * sample_rate,
        nfft=m,
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


def _finite_reals(x: ArrayLike, what: str) -> NDArray[np.float64]:
    a = np.asarray(x)
    if a.ndim != 1 or (a.size and a.dtype.kind not in "iuf"):
        raise ValueError(f"{what} must be a 1-D array of real numbers")
    f = a.astype(np.float64)
    if not np.all(np.isfinite(f)):
        raise ValueError(f"{what} must be finite")
    return f


def lomb_scargle(
    times: ArrayLike,
    values: ArrayLike,
    frequencies: ArrayLike,
    *,
    center: bool = True,
    normalization: str = "standard",
) -> NDArray[np.float64]:
    """Lomb-Scargle periodogram of real ``values`` taken at ``times``, one value per frequency
    (Hz): Scargle's ``P``, or ``2P/sum(y^2)`` for ``"standard"`` (conventions: Spectra)."""
    t = _finite_reals(times, "times")
    y = _finite_reals(values, "values")
    f = _finite_reals(frequencies, "frequencies")
    if t.size != y.size or t.size < 2:
        raise ValueError("times and values must have the same length, at least 2")
    if np.any(f <= 0):
        raise ValueError("frequencies must be positive")
    if normalization not in ("standard", "power"):
        raise ValueError('normalization must be "standard" or "power"')
    if center:
        y = y - np.mean(y)
    out = np.empty(f.size)
    small = 1e-12 * t.size
    for i, fi in enumerate(f):
        w = 2 * math.pi * float(fi)
        s2, c2 = float(np.sum(np.sin(2 * w * t))), float(np.sum(np.cos(2 * w * t)))
        tau = math.atan2(s2, c2) / (2 * w)
        c, s = np.cos(w * (t - tau)), np.sin(w * (t - tau))
        cc, ss = float(np.dot(c, c)), float(np.dot(s, s))
        p = 0.0
        if cc >= small:
            p += float(np.dot(y, c)) ** 2 / cc
        if ss >= small:
            p += float(np.dot(y, s)) ** 2 / ss
        out[i] = p / 2
    if normalization == "standard":
        total = float(np.dot(y, y))
        if not total > 0:
            raise ValueError("the standard normalization needs values that are not all equal")
        out = out * 2 / total
    return out


def lomb_scargle_false_alarm(
    power: float, num_samples: int, *, num_frequencies: int = 1, center: bool = True
) -> float:
    """Chance that white Gaussian noise gives a standard Lomb-Scargle value above ``power`` at any
    of ``num_frequencies`` independent frequencies (conventions: Spectra; ADR 0062)."""
    z = real(power, "power")
    n = count(num_samples, "num_samples")
    m = count(num_frequencies, "num_frequencies")
    d = 3 if center else 2
    if not 0 <= z <= 1:
        raise ValueError("power must be between 0 and 1 (the standard normalization)")
    if n < d + 1:
        raise ValueError(f"num_samples must be at least {d + 1}")
    if m < 1:
        raise ValueError("num_frequencies must be at least 1")
    p1 = (1 - z) ** ((n - d) / 2)
    return 1.0 if p1 == 1 else -math.expm1(m * math.log1p(-p1))


def lomb_scargle_frequencies(
    times: ArrayLike, *, oversampling: float = 5.0, max_frequency: float | None = None
) -> NDArray[np.float64]:
    """Frequency grid ``k / (oversampling * T)``, ``k = 1, 2, ...`` up to ``max_frequency``
    (default ``N / (2T)``), for :func:`lomb_scargle` (conventions: Spectra; ADR 0062)."""
    t = _finite_reals(times, "times")
    if t.size < 2:
        raise ValueError("times must have at least 2 values")
    span = float(np.max(t) - np.min(t))
    if not span > 0:
        raise ValueError("times must not all be equal")
    os_ = real(oversampling, "oversampling")
    fmax = t.size / (2 * span) if max_frequency is None else real(max_frequency, "max_frequency")
    if os_ <= 0 or fmax <= 0:
        raise ValueError("oversampling and max_frequency must be positive")
    df = 1 / (os_ * span)
    ratio = fmax / df + 1e-9
    if not ratio < 10**7 + 1:  # also catches an infinite ratio
        raise ValueError("the grid would have more than 10^7 frequencies")
    k = math.floor(ratio)
    return np.arange(1, k + 1, dtype=np.float64) * df


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
