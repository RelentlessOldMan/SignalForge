"""FFT, frequency axes, windows, Welch PSD, Lomb-Scargle, occupied bandwidth and channel power.

Definitions are in docs/conventions.md (Spectra) and docs/adr/0006-fft-windows-spectra.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from . import _checks, units
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
    return TaperSet(tapers, _concentrations(tapers, nw / n))


def _concentrations(tapers: NDArray[np.float64], w: float) -> NDArray[np.float64]:
    n = tapers.shape[1]
    lag = np.arange(1, n)
    sinc = np.sin(2 * math.pi * w * lag) / (math.pi * lag)
    # each autocorrelation r_d by an FFT of length >= 2N, exact up to rounding
    r = np.fft.irfft(np.abs(np.fft.rfft(tapers, 2 * n, axis=1)) ** 2, 2 * n, axis=1)[:, :n]
    return np.asarray(2 * w * r[:, 0] + 2 * (r[:, 1:] @ sinc), dtype=np.float64)


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
    adaptive: bool = False,
) -> SpectralDensity:
    """Thomson's multitaper PSD: the mean of the periodograms of the whole input under the DPSS
    tapers, in the Welch scaling, or with ``adaptive`` Thomson's adaptive weights (conventions:
    Spectra, Multitaper PSD; ADRs 0078, 0079)."""
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
    eigen = np.array([np.abs(np.fft.fft(v * x, m)) ** 2 / sample_rate for v in tapers])
    if adaptive:
        lam = _concentrations(tapers, nw / n)
        noise = float(np.sum(np.abs(x) ** 2)) / n / sample_rate
        two = _adaptive(eigen, lam, noise)
    else:
        two = np.sum(eigen, axis=0) / k
    g = _Segments(x, n, n, 1, tapers[0], 1.0, bool(one_sided), "none", m)
    return SpectralDensity(
        frequencies=g.frequencies(sample_rate),
        psd=np.asarray(g.fold(two), dtype=np.float64),
        sample_rate=float(sample_rate),
        nperseg=n,
        num_segments=k,
        one_sided=bool(one_sided),
        bin_width=sample_rate / m,
        enbw_hz=2 * nw / n * sample_rate,
        nfft=m,
    )


@dataclass(frozen=True)
class HarmonicFTest:
    """Thomson's harmonic F-test per bin: line amplitudes, F statistics with 2 and
    ``2*num_tapers - 2`` degrees of freedom, and their p-values; see docs/conventions.md (Spectra,
    Harmonic F-test)."""

    frequencies: NDArray[np.float64]
    amplitudes: NDArray[np.complex128]
    f_statistic: NDArray[np.float64]
    p_values: NDArray[np.float64]
    num_tapers: int


def harmonic_f_test(
    samples: ArrayLike,
    sample_rate: float,
    half_bandwidth: float,
    *,
    num_tapers: int | None = None,
    nfft: int | None = None,
) -> HarmonicFTest:
    """Thomson's F-test for a line ``mu*exp(2j*pi*f*n/fs)`` at each bin, by regressing the
    tapered DFTs on the tapers' DC values (conventions: Spectra, Harmonic F-test; ADR 0080)."""
    x = _vector(samples, "samples")
    if not real(sample_rate, "sample_rate") > 0:
        raise ValueError("sample_rate must be positive and finite")
    n = x.size
    if n < 1:
        raise ValueError("samples needs at least 1")
    m = n if nfft is None else count(nfft, "nfft")
    if m < n:
        raise ValueError("nfft must be at least the input length")
    nw, k = _taper_args(n, half_bandwidth, num_tapers)
    if k < 2:
        raise ValueError("the F-test needs at least 2 tapers")
    tapers = _dpss(n, nw / n, k)
    xs = np.array([np.fft.fft(v * x, m) for v in tapers])
    u = np.array([math.fsum(v) for v in tapers])
    uu = math.fsum(u * u)
    mu = np.sum(u[:, None] * xs, axis=0) / uu
    resid = np.sum(np.abs(xs - mu[None, :] * u[:, None]) ** 2, axis=0)
    num = (k - 1) * np.abs(mu) ** 2 * uu
    with np.errstate(divide="ignore", invalid="ignore"):
        f = np.where(resid > 0, num / resid, np.where(num > 0, math.inf, 0.0))
    p_val = np.where(np.isinf(f), 0.0, (1 + f / (k - 1)) ** -(k - 1))
    if np.iscomplexobj(x):
        sel = np.fft.fftshift(np.arange(m))
    else:
        sel = np.arange(m // 2 + 1)
    g = _Segments(x, n, n, 1, tapers[0], 1.0, not np.iscomplexobj(x), "none", m)
    return HarmonicFTest(
        frequencies=g.frequencies(sample_rate),
        amplitudes=np.asarray(mu[sel], dtype=np.complex128),
        f_statistic=np.asarray(f[sel], dtype=np.float64),
        p_values=np.asarray(p_val[sel], dtype=np.float64),
        num_tapers=k,
    )


@dataclass(frozen=True)
class LineRemoval:
    """Lines found by the harmonic F-test and the multitaper PSD left once they are removed
    (conventions: Spectra, Multitaper line removal; ADR 0083)."""

    spectrum: SpectralDensity
    line_frequencies: NDArray[np.float64]
    line_amplitudes: NDArray[np.complex128]
    residual: NDArray[np.float64] | NDArray[np.complex128]


def multitaper_line_removal(
    samples: ArrayLike,
    sample_rate: float,
    half_bandwidth: float,
    *,
    probability: float | None = None,
    num_tapers: int | None = None,
    one_sided: bool | None = None,
    nfft: int | None = None,
    adaptive: bool = False,
) -> LineRemoval:
    """Thomson's line removal: subtract the lines the harmonic F-test finds, then the multitaper
    PSD of what remains (conventions: Spectra, Multitaper line removal; ADR 0083)."""
    x = _vector(samples, "samples")
    test = harmonic_f_test(x, sample_rate, half_bandwidth, num_tapers=num_tapers, nfft=nfft)
    n = x.size
    alpha = 1 / n if probability is None else real(probability, "probability")
    if not 0 < alpha <= 1:
        raise ValueError("probability must be in (0, 1]")
    m = n if nfft is None else int(nfft)
    nw, _ = _taper_args(n, half_bandwidth, num_tapers)
    r = math.floor(nw * m / n)
    is_complex = np.iscomplexobj(x)

    def pos(b: int) -> int:
        b %= m
        if is_complex:
            return (b + m // 2) % m
        return b if b <= m // 2 else m - b

    f, p = test.f_statistic, test.p_values
    lines = []
    for j in range(f.size):
        if not p[j] < alpha:
            continue
        b = (j - m // 2) % m if is_complex else j
        window = (pos(b + d) for d in range(-r, r + 1) if d)
        if all(f[j] > f[i] if i < j else f[j] >= f[i] for i in window if i != j):
            lines.append(j)
    t = np.arange(n)
    residual = x.copy()
    for j in lines:
        b = (j - m // 2) % m if is_complex else j
        e = np.exp(2j * np.pi * ((b * t) % m) / m)
        mu = test.amplitudes[j]
        if is_complex:
            residual -= mu * e
        elif b == 0 or 2 * b == m:
            residual -= mu.real * e.real
        else:
            residual -= 2 * (mu * e).real
    spectrum = multitaper_psd(
        residual,
        sample_rate,
        half_bandwidth,
        num_tapers=num_tapers,
        one_sided=one_sided,
        nfft=nfft,
        adaptive=adaptive,
    )
    return LineRemoval(
        spectrum=spectrum,
        line_frequencies=np.asarray(test.frequencies[lines], dtype=np.float64),
        line_amplitudes=np.asarray(test.amplitudes[lines], dtype=np.complex128),
        residual=residual,
    )


def _adaptive(
    eigen: NDArray[np.float64], lam: NDArray[np.float64], noise: float
) -> NDArray[np.float64]:
    """Thomson's adaptive combination, each bin iterated on its own (ADR 0079)."""
    s: NDArray[np.float64] = np.array(eigen[0] if len(lam) == 1 else (eigen[0] + eigen[1]) / 2)
    if noise == 0 or len(lam) == 1:
        return s
    live = s > 0
    for _ in range(1000):
        if not live.any():
            break
        cur = s[live]
        w = lam[:, None] / (lam[:, None] * cur + (1 - lam[:, None]) * noise) ** 2
        new = np.sum(w * eigen[:, live], axis=0) / np.sum(w, axis=0)
        s[live] = new
        done = np.abs(new - cur) <= 1e-10 * new
        idx = np.flatnonzero(live)
        live[idx[done]] = False
    return s


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


def generalized_lomb_scargle(
    times: ArrayLike,
    values: ArrayLike,
    frequencies: ArrayLike,
    *,
    uncertainties: ArrayLike | None = None,
    normalization: str = "standard",
) -> NDArray[np.float64]:
    """Zechmeister-Kuerster generalized Lomb-Scargle periodogram: the weighted fit of
    ``a cos + b sin + c`` at each frequency (Hz), as the fraction ``(chi2_0 - chi2)/chi2_0`` or for
    ``"power"`` half the drop in chi2 (conventions: Spectra, Generalized Lomb-Scargle; ADR 0081)."""
    t = _finite_reals(times, "times")
    y = _finite_reals(values, "values")
    f = _finite_reals(frequencies, "frequencies")
    if t.size != y.size or t.size < 2:
        raise ValueError("times and values must have the same length, at least 2")
    if uncertainties is None:
        inv = np.ones(t.size)
    else:
        sigma = _finite_reals(uncertainties, "uncertainties")
        if sigma.size != t.size or np.any(sigma <= 0):
            raise ValueError("uncertainties must be positive, one per sample")
        inv = 1 / sigma**2
    if np.any(f <= 0):
        raise ValueError("frequencies must be positive")
    if normalization not in ("standard", "power"):
        raise ValueError('normalization must be "standard" or "power"')
    big_w = float(np.sum(inv))
    w = inv / big_w
    mean = float(np.dot(w, y))
    yy = float(np.dot(w, y * y)) - mean * mean
    if normalization == "standard" and not yy > 0:
        raise ValueError("the standard normalization needs values that are not all equal")

    def cov(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
        return float(np.dot(w, a * b)) - float(np.dot(w, a)) * float(np.dot(w, b))

    out = np.empty(f.size)
    for i, fi in enumerate(f):
        om = 2 * math.pi * float(fi)
        c0, s0 = np.cos(om * t), np.sin(om * t)
        tau = math.atan2(2 * cov(c0, s0), cov(c0, c0) - cov(s0, s0)) / (2 * om)
        c, s = np.cos(om * (t - tau)), np.sin(om * (t - tau))
        cc, ss = cov(c, c), cov(s, s)
        p = 0.0
        if cc >= 1e-12:
            p += cov(y, c) ** 2 / cc
        if ss >= 1e-12:
            p += cov(y, s) ** 2 / ss
        out[i] = p / yy if normalization == "standard" else big_w * p / 2
    return out


def lomb_scargle_multiterm(
    times: ArrayLike,
    values: ArrayLike,
    frequencies: ArrayLike,
    terms: int,
    *,
    uncertainties: ArrayLike | None = None,
    normalization: str = "standard",
) -> NDArray[np.float64]:
    """The weighted fit of a constant and ``terms`` harmonics at each frequency (Hz), as the
    fraction ``(chi2_0 - chi2)/chi2_0`` or for ``"power"`` half the drop in chi2 (conventions:
    Spectra, Multiterm Lomb-Scargle; ADR 0103)."""
    t = _finite_reals(times, "times")
    y = _finite_reals(values, "values")
    f = _finite_reals(frequencies, "frequencies")
    if t.size != y.size or t.size < 2:
        raise ValueError("times and values must have the same length, at least 2")
    k_max = count(terms, "terms")
    if k_max < 1:
        raise ValueError("terms must be at least 1")
    if uncertainties is None:
        inv = np.ones(t.size)
    else:
        sigma = _finite_reals(uncertainties, "uncertainties")
        if sigma.size != t.size or np.any(sigma <= 0):
            raise ValueError("uncertainties must be positive, one per sample")
        inv = 1 / sigma**2
    if np.any(f <= 0):
        raise ValueError("frequencies must be positive")
    if normalization not in ("standard", "power"):
        raise ValueError('normalization must be "standard" or "power"')
    big_w = float(np.sum(inv))
    w = inv / big_w
    yc = y - float(np.dot(w, y))
    yy = float(np.dot(w, yc * yc))
    # the weights need not sum to exactly 1, so equal values can leave a tiny yy
    if normalization == "standard" and (np.all(y == y[0]) or not yy > 0):
        raise ValueError("the standard normalization needs values that are not all equal")
    out = np.empty(f.size)
    for i, fi in enumerate(f):
        om = 2 * math.pi * float(fi)
        kept: list[tuple[NDArray[np.float64], float]] = []
        explained = 0.0
        for k in range(1, k_max + 1):
            arg = om * k * t
            for column in (np.cos(arg), np.sin(arg)):
                q = column - float(np.dot(w, column))
                for b, bb in kept:
                    q = q - (float(np.dot(w, q * b)) / bb) * b
                qq = float(np.dot(w, q * q))
                if qq < 1e-12:
                    continue
                kept.append((q, qq))
                explained += float(np.dot(w, yc * q)) ** 2 / qq
        out[i] = explained / yy if normalization == "standard" else big_w * explained / 2
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


def lomb_scargle_false_alarm_level(
    probability: float, num_samples: int, *, num_frequencies: int = 1, center: bool = True
) -> float:
    """The standard Lomb-Scargle value that white Gaussian noise exceeds with chance
    ``probability`` over ``num_frequencies`` independent frequencies: the inverse of
    ``lomb_scargle_false_alarm`` (conventions: Spectra; ADR 0082)."""
    p = real(probability, "probability")
    n = count(num_samples, "num_samples")
    m = count(num_frequencies, "num_frequencies")
    d = 3 if center else 2
    if not 0 <= p <= 1:
        raise ValueError("probability must be between 0 and 1")
    if n < d + 1:
        raise ValueError(f"num_samples must be at least {d + 1}")
    if m < 1:
        raise ValueError("num_frequencies must be at least 1")
    if p == 0:
        return 1.0
    p1 = -math.expm1(math.log1p(-p) / m) if p < 1 else 1.0
    return -math.expm1(2 * math.log(p1) / (n - d))


def lomb_scargle_false_alarm_baluev(
    power: float, times: ArrayLike, max_frequency: float, *, center: bool = True
) -> float:
    """Baluev's alias-free estimate of the chance that white Gaussian noise gives a standard
    Lomb-Scargle value above ``power`` anywhere up to ``max_frequency`` for these sample times
    (conventions: Spectra; ADR 0098)."""
    z = real(power, "power")
    if not 0 <= z <= 1:
        raise ValueError("power must be between 0 and 1 (the standard normalization)")
    return _baluev(z, *_baluev_setup(times, max_frequency, center))


def lomb_scargle_bootstrap(
    times: ArrayLike,
    values: ArrayLike,
    frequencies: ArrayLike,
    draws: int,
    *,
    seed: int | np.random.Generator,
    center: bool = True,
) -> NDArray[np.float64]:
    """The highest standard Lomb-Scargle value over ``frequencies`` for each of ``draws``
    resamplings of ``values`` with replacement at the same ``times``, in draw order
    (conventions: Spectra; ADR 0101)."""
    lomb_scargle(times, values, frequencies, center=center)  # checks everything else
    t = np.asarray(times, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.size == 0:
        raise ValueError("frequencies must not be empty")
    k = count(draws, "draws")
    if k < 1:
        raise ValueError("draws must be at least 1")
    rng = (
        seed
        if isinstance(seed, np.random.Generator)
        else np.random.default_rng(count(seed, "seed"))
    )
    n = y.size
    peaks = np.zeros(k)
    for i in range(k):
        drawn = y[rng.integers(0, n, size=n)]
        if np.all(drawn == drawn[0]) if center else not np.any(drawn):
            continue  # nothing to normalize: the peak is 0
        peaks[i] = float(np.max(lomb_scargle(t, drawn, f, center=center)))
    return peaks


def lomb_scargle_false_alarm_level_baluev(
    probability: float, times: ArrayLike, max_frequency: float, *, center: bool = True
) -> float:
    """The standard Lomb-Scargle value that white Gaussian noise exceeds with chance
    ``probability`` anywhere up to ``max_frequency``: the inverse of
    :func:`lomb_scargle_false_alarm_baluev`, by bisection (conventions: Spectra; ADR 0099)."""
    p = real(probability, "probability")
    if not 0 <= p <= 1:
        raise ValueError("probability must be between 0 and 1")
    setup = _baluev_setup(times, max_frequency, center)
    if p == 1:
        return 0.0  # F(0) = 1 is not above 1
    lo, hi = 0.0, 1.0
    while True:
        m = lo + (hi - lo) / 2
        if m in (lo, hi):
            return hi
        if _baluev(m, *setup) > p:
            lo = m
        else:
            hi = m


def _baluev_setup(times: ArrayLike, max_frequency: float, center: bool) -> tuple[int, int, float]:
    """Checks the times and ``f_max``; returns ``N_K``, ``N_H`` and ``f_max·√(4πD)`` times gamma."""
    t = _finite_reals(times, "times")
    fmax = real(max_frequency, "max_frequency")
    d, h = (3, 1) if center else (2, 0)
    n = t.size
    if n < d + 1:
        raise ValueError(f"times must have at least {d + 1} values")
    if not float(np.max(t) - np.min(t)) > 0:
        raise ValueError("times must not all be equal")
    if fmax <= 0:
        raise ValueError("max_frequency must be positive")
    nk, nh = n - d, n - h
    mean = float(np.mean(t))
    var = float(np.mean((t - mean) ** 2))
    k, r = (2, 1 / math.sqrt(math.pi)) if nh % 2 == 0 else (3, math.sqrt(math.pi) / 2)
    while k < nh:
        r = r * k / (k - 1)
        k += 2
    gamma = math.sqrt(2 / nh) * r
    return nk, nh, fmax * math.sqrt(4 * math.pi * var) * gamma


def _baluev(z: float, nk: int, nh: int, scale: float) -> float:
    """The Baluev value at ``z`` for the numbers from :func:`_baluev_setup`."""
    p1 = (1 - z) ** (nk / 2)
    if p1 == 1:
        return 1.0
    tau = scale * (1 - z) ** ((nk - 1) / 2)
    tau *= math.sqrt(nh * z / 2)
    return -math.expm1(math.log1p(-p1) - tau)


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


@dataclass(frozen=True)
class NoisePowerRatio:
    """Loaded and notch power densities and their ratio (conventions: Spectra, Noise power
    ratio; ADR 0118). Densities are in the PSD's units."""

    loaded_density: float
    notch_density: float
    npr_db: float


def noise_power_ratio(
    frequencies: ArrayLike,
    psd: ArrayLike,
    band: ArrayLike,
    notch: ArrayLike,
    *,
    span: Span | ArrayLike | None = None,
) -> NoisePowerRatio:
    """Mean PSD of the loaded ``band`` outside the ``notch`` over the mean PSD in the notch, each
    by the channel power rule; ``band = (low, high)`` and ``notch = (low, high)`` in Hz."""
    b = np.asarray(band, dtype=np.float64)
    n = np.asarray(notch, dtype=np.float64)
    if b.shape != (2,) or n.shape != (2,):
        raise ValueError("band and notch must each be (low, high)")
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(n))):
        raise ValueError("band and notch edges must be finite")
    b_lo, b_hi, n_lo, n_hi = float(b[0]), float(b[1]), float(n[0]), float(n[1])
    if not b_lo < n_lo < n_hi < b_hi:
        raise ValueError("need band low < notch low < notch high < band high")
    power, left, right = _bins(frequencies, psd, span)
    slack = 1e-9 * float(np.max(right - left))  # as for acpr
    if b_lo < left[0] - slack or b_hi > right[-1] + slack:
        raise ValueError(f"band [{b_lo}, {b_hi}] leaves the spectrum [{left[0]}, {right[-1]}]")

    def channel(low: float, high: float) -> float:
        overlap = np.clip(np.minimum(right, high) - np.maximum(left, low), 0.0, None)
        return float(np.sum(power * overlap / (right - left)))

    loaded = (channel(b_lo, n_lo) + channel(n_hi, b_hi)) / ((n_lo - b_lo) + (b_hi - n_hi))
    if not loaded > 0:
        raise ValueError("the loaded band has no power")
    inside = channel(n_lo, n_hi) / (n_hi - n_lo)
    npr = math.inf if inside == 0 else 10 * (math.log10(loaded) - math.log10(inside))
    return NoisePowerRatio(loaded, inside, npr)


@dataclass(frozen=True)
class SpectralFlatness:
    """Geometric and arithmetic mean of the PSD over a band, and their ratio (conventions:
    Spectra, Spectral flatness; ADR 0120). Means are in the PSD's units."""

    geometric_mean: float
    arithmetic_mean: float
    flatness: float
    flatness_db: float


@dataclass(frozen=True)
class SpectralCrest:
    """Peak and mean of the PSD over a band, and their ratio (conventions: Spectra, Spectral
    crest factor; ADR 0125). Peak and mean are in the PSD's units."""

    peak: float
    mean: float
    crest: float
    crest_db: float


@dataclass(frozen=True)
class SpectralShape:
    """Skewness and kurtosis of a PSD over a band (conventions: Spectra, Spectral skewness and
    kurtosis; ADR 0126). The kurtosis is not the excess: a flat band gives 9/5."""

    skewness: float
    kurtosis: float


@dataclass(frozen=True)
class SpectralSlope:
    """The least-squares line through a PSD over a band (conventions: Spectra, Spectral slope;
    ADR 0127): ``level`` at ``center`` Hz, ``slope`` per Hz, in the PSD's units or dB."""

    center: float
    level: float
    slope: float


@dataclass(frozen=True)
class HarmonicCentroid:
    """The amplitude-weighted mean frequency of the harmonic tones and their spread about it,
    both in Hz (conventions: Spectra, Harmonic centroid; ADR 0145)."""

    centroid: float
    spread: float


@dataclass(frozen=True)
class Tristimulus:
    """The share of harmonic amplitude in the fundamental (``first``), orders 2-4 (``second``)
    and orders 5 and up (``third``) (conventions: Spectra, Tristimulus; ADR 0142)."""

    first: float
    second: float
    third: float


@dataclass(frozen=True)
class HarmonicSeries:
    """The fundamental that best explains a list of tones (conventions: Spectra, Harmonic
    series; ADR 0139): its least-squares ``fundamental``, each tone's harmonic ``orders`` (0 when
    unmatched), and how many tones ``matched``."""

    fundamental: float
    orders: NDArray[np.int64]
    matched: int


@dataclass(frozen=True)
class PeakWidth:
    """A peak's width at a level below its top (conventions: Spectra, Peak widths; ADR 0138):
    its bin ``index``, the ``level``, the crossings ``left`` and ``right`` in Hz, and the
    ``width`` between them."""

    index: int
    level: float
    left: float
    right: float
    width: float


@dataclass(frozen=True)
class Tone:
    """A tone found in a PSD (conventions: Spectra, Find tones; ADR 0137): its peak bin
    ``index``, its interpolated ``frequency`` and ``height``, and its peak's ``prominence``."""

    index: int
    frequency: float
    height: float
    prominence: float


@dataclass(frozen=True)
class PeakEstimate:
    """A peak's vertex from a parabola through three bins (conventions: Spectra, Peak
    interpolation; ADR 0136): its ``frequency``, its ``height``, and its ``offset`` in bins."""

    frequency: float
    height: float
    offset: float


@dataclass(frozen=True)
class SpectralPeak:
    """A local maximum of a PSD (conventions: Spectra, Spectral peaks; ADR 0135): its middle
    bin ``index``, the ``frequency`` at its middle, its ``height`` and its ``prominence``."""

    index: int
    frequency: float
    height: float
    prominence: float


@dataclass(frozen=True)
class HarmonicToNoise:
    """The power at a fundamental's harmonics and everywhere else (conventions: Spectra,
    Harmonic-to-noise ratio; ADR 0143): ``harmonic`` and ``noise``, ``ratio = harmonic / noise``
    and ``ratio_db`` in dB."""

    harmonic: float
    noise: float
    ratio: float
    ratio_db: float


@dataclass(frozen=True)
class BandEnergyRatio:
    """The power above and below a split frequency (conventions: Spectra, Band energy ratio;
    ADR 0134): ``low`` and ``high``, ``ratio = high / low`` and ``ratio_db`` in dB."""

    low: float
    high: float
    ratio: float
    ratio_db: float


@dataclass(frozen=True)
class SpectralContrast:
    """The loudest and quietest parts of a band (conventions: Spectra, Spectral contrast; ADR
    0133): the mean densities ``peak`` and ``valley`` over the top and bottom fraction of the
    band's width, and ``contrast_db = 10 log10(peak / valley)``."""

    peak: float
    valley: float
    contrast_db: float


@dataclass(frozen=True)
class SpectralEntropy:
    """Differential entropy of a band's normalized PSD (conventions: Spectra, Spectral entropy;
    ADR 0128): ``entropy`` in nats, ``entropy_bandwidth = exp(entropy)`` in Hz, and that over
    the band's width as ``normalized``."""

    entropy: float
    entropy_bandwidth: float
    normalized: float


def _band_edges(
    band: ArrayLike | None, left: NDArray[np.float64], right: NDArray[np.float64]
) -> tuple[float, float]:
    """The band's edges, checked as for ACPR's channels; the whole spectrum for None."""
    if band is None:
        return float(left[0]), float(right[-1])
    b = np.asarray(band, dtype=np.float64)
    if b.shape != (2,) or not np.all(np.isfinite(b)):
        raise ValueError("band must be (low, high) with finite edges")
    lo, hi = float(b[0]), float(b[1])
    if not lo < hi:
        raise ValueError("band low must be below band high")
    slack = 1e-9 * float(np.max(right - left))  # as for acpr
    if lo < left[0] - slack or hi > right[-1] + slack:
        raise ValueError(f"band [{lo}, {hi}] leaves the spectrum [{left[0]}, {right[-1]}]")
    return lo, hi


@dataclass(frozen=True)
class SpectralMoments:
    """Power, centroid and RMS bandwidth of a PSD over a band (conventions: Spectra, Spectral
    centroid and RMS bandwidth; ADR 0121). Frequencies are in the PSD's axis."""

    power: float
    centroid: float
    rms_bandwidth: float


def spectral_moments(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> SpectralMoments:
    """Power, centroid and RMS bandwidth of the PSD taken as constant over each bin, integrated
    exactly over ``band = (low, high)`` in Hz (the whole spectrum by default)."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    a, b, d = a[keep], b[keep], (power / (right - left))[keep]
    total = float(np.sum(d * (b - a)))
    if not total > 0:
        raise ValueError("the band has no power")
    c = float(np.sum(d * (b - a) * (a + b) / 2)) / total
    var = float(np.sum(d * ((b - c) ** 3 - (a - c) ** 3) / 3)) / total
    return SpectralMoments(total, c, math.sqrt(max(var, 0.0)))


def spectral_shape(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> SpectralShape:
    """Skewness and kurtosis of the PSD taken as constant over each bin, integrated exactly about
    the centroid over ``band = (low, high)`` in Hz (the whole spectrum by default)."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    a, b, d = a[keep], b[keep], (power / (right - left))[keep]
    total = float(np.sum(d * (b - a)))
    if not total > 0:
        raise ValueError("the band has no power")
    c = float(np.sum(d * (b - a) * (a + b) / 2)) / total
    m2, m3, m4 = (
        float(np.sum(d * ((b - c) ** (j + 1) - (a - c) ** (j + 1)) / (j + 1))) / total
        for j in (2, 3, 4)
    )
    if not m2 > 0:
        raise ValueError("the band has no spread")
    return SpectralShape(m3 / m2**1.5, m4 / (m2 * m2))


def spectral_slope(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
    db: bool = False,
) -> SpectralSlope:
    """The continuous least-squares line through the PSD, taken as constant over each bin (in dB
    with ``db``), over ``band = (low, high)`` in Hz (the whole spectrum by default)."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    a, b, d = a[keep], b[keep], (power / (right - left))[keep]
    if not float(np.sum(d * (b - a))) > 0:
        raise ValueError("the band has no power")
    if db:
        if np.any(d == 0):
            raise ValueError("with db, every bin in the band must have a positive PSD")
        d = 10 * np.log10(d)
    center, width = (lo + hi) / 2, hi - lo
    level = float(np.sum(d * (b - a))) / width
    moment = float(np.sum(d * ((b - center) ** 2 - (a - center) ** 2) / 2))
    return SpectralSlope(center, level, moment / (width**3 / 12))


def spectral_decrease(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> float:
    """How fast the PSD falls from the band's first bin: each later piece's change in density
    over its distance in bins, weighted by width, over the later pieces' power (conventions:
    Spectra, Spectral decrease; ADR 0130)."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    f = np.asarray(frequencies, dtype=float)
    step = float(f[1] - f[0])
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    a, b, d = a[keep], b[keep], (power / (right - left))[keep]
    if d.size < 2:
        raise ValueError("the band must hold at least two bins")
    w, m = b - a, (a + b) / 2
    rest = float(np.sum(d[1:] * w[1:]))
    if not rest > 0:
        raise ValueError("the band has no power after its first bin")
    return float(np.sum((d[1:] - d[0]) * w[1:] * step / (m[1:] - m[0]))) / rest


def spectral_peaks(
    frequencies: ArrayLike, psd: ArrayLike, *, min_prominence: float = 0.0
) -> list[SpectralPeak]:
    """The PSD's local maxima with their prominence, in order of frequency; a plateau is one
    peak, and the first and last bins are never peaks."""
    floor = real(min_prominence, "min_prominence")
    if floor < 0:
        raise ValueError("min_prominence must be >= 0")
    _bins(frequencies, psd, None)
    f = np.asarray(frequencies, dtype=float)
    x = [float(v) for v in np.asarray(psd, dtype=float)]
    n = len(x)
    out = []
    i = 1
    while i < n - 1:
        j = i
        while j + 1 < n and x[j + 1] == x[i]:
            j += 1
        h = x[i]
        if x[i - 1] < h and j < n - 1 and x[j + 1] < h:
            lo_left = h
            k = i
            while k >= 0 and x[k] <= h:
                lo_left = min(lo_left, x[k])
                k -= 1
            lo_right = h
            k = j
            while k < n and x[k] <= h:
                lo_right = min(lo_right, x[k])
                k += 1
            prom = h - max(lo_left, lo_right)
            if prom >= floor:
                out.append(SpectralPeak((i + j) // 2, float(f[i] + f[j]) / 2, h, prom))
        i = j + 1
    return out


def interpolate_peak(
    frequencies: ArrayLike, psd: ArrayLike, index: int, *, scale: str = "db"
) -> PeakEstimate:
    """The vertex of the parabola through the peak bin ``index`` and its neighbours, fitted to
    the PSD in dB (``"db"``) or as it is (``"linear"``)."""
    if scale not in ("db", "linear"):
        raise ValueError('scale must be "db" or "linear"')
    k = count(index, "index")
    _bins(frequencies, psd, None)
    f = np.asarray(frequencies, dtype=float)
    x = np.asarray(psd, dtype=float)
    n = f.size
    if not 1 <= k <= n - 2:
        raise ValueError("index must be an interior bin, 1 <= index <= n - 2")
    if x[k] < x[k - 1] or x[k] < x[k + 1]:
        raise ValueError("the bin at index must not be lower than its neighbours")
    if scale == "db" and not min(x[k - 1 : k + 2]) > 0:
        raise ValueError("the three bins must be positive on the dB scale")
    got = _vertex(f, x, k, scale)
    if got is None:
        raise ValueError("the three bins are flat")
    return got


def _vertex(
    f: NDArray[np.float64], x: NDArray[np.float64], k: int, scale: str
) -> PeakEstimate | None:
    """The parabola's vertex through bins ``k - 1, k, k + 1``, or None where it is undefined."""
    a, b, c = float(x[k - 1]), float(x[k]), float(x[k + 1])
    if scale == "db":
        if not min(a, b, c) > 0:
            return None
        a, b, c = 10 * math.log10(a), 10 * math.log10(b), 10 * math.log10(c)
    curve = a - 2 * b + c
    if not curve < 0:
        return None
    offset = (a - c) / (2 * curve)
    vertex = b - (a - c) * offset / 4
    delta = float(f[-1] - f[0]) / (f.size - 1)
    height = 10 ** (vertex / 10) if scale == "db" else vertex
    return PeakEstimate(float(f[k]) + offset * delta, height, offset)


def peak_widths(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    rel_height: float = 0.5,
    min_prominence: float = 0.0,
) -> list[PeakWidth]:
    """Each spectral peak's width where the PSD crosses ``height - rel_height*prominence``,
    interpolated linearly between bins; in order of frequency."""
    r = real(rel_height, "rel_height")
    if not 0 < r <= 1:
        raise ValueError("rel_height must be in (0, 1]")
    peaks = spectral_peaks(frequencies, psd, min_prominence=min_prominence)
    f = np.asarray(frequencies, dtype=np.float64)
    x = [float(v) for v in np.asarray(psd, dtype=np.float64)]
    n = len(x)
    delta = float(f[-1] - f[0]) / (n - 1)
    out = []
    for p in peaks:
        level = p.height - r * p.prominence
        i = j = p.index
        while x[i - 1] == p.height:
            i -= 1
        while x[j + 1] == p.height:
            j += 1
        k = i
        while k > 0 and x[k] > level:
            k -= 1
        lo = k + (level - x[k]) / (x[k + 1] - x[k]) if x[k] <= level else float(k)
        k = j
        while k < n - 1 and x[k] > level:
            k += 1
        hi = k - (level - x[k]) / (x[k - 1] - x[k]) if x[k] <= level else float(k)
        left, right = float(f[0]) + lo * delta, float(f[0]) + hi * delta
        out.append(PeakWidth(p.index, level, left, right, right - left))
    return out


def harmonic_series(
    frequencies: ArrayLike, tolerance: float, *, max_order: int = 10
) -> HarmonicSeries:
    """The candidate ``t_i/m`` that matches the most tones within ``tolerance`` Hz (ties to the
    highest), refined by least squares over its matched tones."""
    t = np.asarray(frequencies, dtype=np.float64)
    if t.ndim != 1 or t.size < 1:
        raise ValueError("frequencies must be a 1-D array of at least one tone")
    if not (np.all(np.isfinite(t)) and np.all(t > 0)):
        raise ValueError("frequencies must be finite and positive")
    tol = real(tolerance, "tolerance")
    if not tol > 0:
        raise ValueError("tolerance must be > 0")
    top = count(max_order, "max_order")
    if top < 1:
        raise ValueError("max_order must be at least 1")
    tones = [float(v) for v in t]

    def orders_for(c: float) -> list[int]:
        out = []
        for v in tones:
            m = math.floor(v / c + 0.5)
            out.append(m if 1 <= m <= top and abs(v - m * c) <= tol else 0)
        return out

    best_c, best_orders, best_n = 0.0, [0] * len(tones), -1
    for v in tones:
        for m in range(1, top + 1):
            c = v / m
            orders = orders_for(c)
            n = sum(1 for o in orders if o)
            if n > best_n or (n == best_n and c > best_c):
                best_c, best_orders, best_n = c, orders, n
    num = sum(o * v for o, v in zip(best_orders, tones, strict=True))
    den = sum(o * o for o in best_orders)
    return HarmonicSeries(num / den, np.array(best_orders, dtype=np.int64), best_n)


def inharmonicity(
    frequencies: ArrayLike, heights: ArrayLike, fundamental: float, orders: ArrayLike
) -> float:
    """``(2/f0)·Σ h|t - m·f0| / Σ h`` over the tones with order ``m >= 1``: 0 for exact
    harmonics, 1 for partials half a fundamental away."""
    t = np.asarray(frequencies, dtype=np.float64)
    h = np.asarray(heights, dtype=np.float64)
    m = np.asarray(orders, dtype=np.float64)
    if t.ndim != 1 or h.shape != t.shape or m.shape != t.shape:
        raise ValueError("frequencies, heights and orders must be 1-D arrays of the same length")
    if not (np.all(np.isfinite(t)) and np.all(t > 0)):
        raise ValueError("frequencies must be finite and positive")
    if not (np.all(np.isfinite(h)) and np.all(h >= 0)):
        raise ValueError("heights must be finite and non-negative")
    if not (np.all(np.isfinite(m)) and np.all(m >= 0) and np.all(m == np.floor(m))):
        raise ValueError("orders must be whole numbers >= 0")
    f0 = real(fundamental, "fundamental")
    if not f0 > 0:
        raise ValueError("fundamental must be > 0")
    use = m >= 1
    total = float(np.sum(h[use]))
    if not total > 0:
        raise ValueError("the matched tones' heights must sum to more than 0")
    spread = float(np.sum(h[use] * np.abs(t[use] - m[use] * f0)))
    return 2 / f0 * spread / total


def odd_even_ratio(heights: ArrayLike, orders: ArrayLike) -> float:
    """The power in odd harmonic orders (the fundamental counts as odd) over the power in even
    ones; order 0 is left out, and no even power gives ``inf``."""
    h = np.asarray(heights, dtype=np.float64)
    m = np.asarray(orders, dtype=np.float64)
    if h.ndim != 1 or m.shape != h.shape:
        raise ValueError("heights and orders must be 1-D arrays of the same length")
    if not (np.all(np.isfinite(h)) and np.all(h >= 0)):
        raise ValueError("heights must be finite and non-negative")
    if not (np.all(np.isfinite(m)) and np.all(m >= 0) and np.all(m == np.floor(m))):
        raise ValueError("orders must be whole numbers >= 0")
    odd = float(np.sum(h[m % 2 == 1]))
    even = float(np.sum(h[(m >= 2) & (m % 2 == 0)]))
    if even > 0:
        return odd / even
    if odd > 0:
        return math.inf
    raise ValueError("the harmonics' heights must sum to more than 0")


def tristimulus(heights: ArrayLike, orders: ArrayLike) -> Tristimulus:
    """The shares of harmonic amplitude ``sqrt(height)`` in order 1, orders 2-4 and orders 5 and
    up; order 0 is left out."""
    h = np.asarray(heights, dtype=np.float64)
    m = np.asarray(orders, dtype=np.float64)
    if h.ndim != 1 or m.shape != h.shape:
        raise ValueError("heights and orders must be 1-D arrays of the same length")
    if not (np.all(np.isfinite(h)) and np.all(h >= 0)):
        raise ValueError("heights must be finite and non-negative")
    if not (np.all(np.isfinite(m)) and np.all(m >= 0) and np.all(m == np.floor(m))):
        raise ValueError("orders must be whole numbers >= 0")
    a = np.sqrt(h)
    first = float(np.sum(a[m == 1]))
    second = float(np.sum(a[(m >= 2) & (m <= 4)]))
    third = float(np.sum(a[m >= 5]))
    total = first + second + third
    if not total > 0:
        raise ValueError("the harmonics' heights must sum to more than 0")
    return Tristimulus(first / total, second / total, third / total)


def harmonic_deviation(heights: ArrayLike, orders: ArrayLike) -> float:
    """``Σ|a_m - e_m| / Σ a_m`` over orders ``1..H``, with amplitudes ``a_m = sqrt(Σ height)`` per
    order (0 when missing) and ``e_m`` the mean of ``a_m`` and its neighbours inside ``1..H``."""
    h = np.asarray(heights, dtype=np.float64)
    m = np.asarray(orders, dtype=np.float64)
    if h.ndim != 1 or m.shape != h.shape:
        raise ValueError("heights and orders must be 1-D arrays of the same length")
    if not (np.all(np.isfinite(h)) and np.all(h >= 0)):
        raise ValueError("heights must be finite and non-negative")
    if not (np.all(np.isfinite(m)) and np.all(m >= 0) and np.all(m == np.floor(m))):
        raise ValueError("orders must be whole numbers >= 0")
    top = int(np.max(m)) if m.size else 0
    if top < 1:
        raise ValueError("no tone has an order >= 1")
    power = np.zeros(top + 1)
    np.add.at(power, m.astype(np.int64), h)
    a = np.sqrt(power[1:])
    total = float(np.sum(a))
    if not total > 0:
        raise ValueError("the harmonics' heights must sum to more than 0")
    padded = np.concatenate(([0.0], a, [0.0]))
    counts = np.full(top, 3.0)
    counts[0] -= 1
    counts[-1] -= 1  # with one order, both ends are the same: 1
    envelope = (padded[:-2] + padded[1:-1] + padded[2:]) / counts
    return float(np.sum(np.abs(a - envelope))) / total


def harmonic_centroid(
    frequencies: ArrayLike, heights: ArrayLike, orders: ArrayLike
) -> HarmonicCentroid:
    """The ``sqrt(height)``-weighted mean of the tone frequencies with order ``>= 1``, and their
    weighted standard deviation about it."""
    t = np.asarray(frequencies, dtype=np.float64)
    h = np.asarray(heights, dtype=np.float64)
    m = np.asarray(orders, dtype=np.float64)
    if t.ndim != 1 or h.shape != t.shape or m.shape != t.shape:
        raise ValueError("frequencies, heights and orders must be 1-D arrays of the same length")
    if not (np.all(np.isfinite(t)) and np.all(t > 0)):
        raise ValueError("frequencies must be finite and positive")
    if not (np.all(np.isfinite(h)) and np.all(h >= 0)):
        raise ValueError("heights must be finite and non-negative")
    if not (np.all(np.isfinite(m)) and np.all(m >= 0) and np.all(m == np.floor(m))):
        raise ValueError("orders must be whole numbers >= 0")
    use = m >= 1
    a, f = np.sqrt(h[use]), t[use]
    total = float(np.sum(a))
    if not total > 0:
        raise ValueError("the matched tones' heights must sum to more than 0")
    centroid = float(np.sum(a * f)) / total
    spread = math.sqrt(float(np.sum(a * (f - centroid) ** 2)) / total)
    return HarmonicCentroid(centroid, spread)


def real_cepstrum(samples: ArrayLike, nfft: int | None = None) -> NDArray[np.float64]:
    """``Re IFFT(ln|FFT(x, nfft)|)``: the real cepstrum, ``nfft`` values (conventions: Spectra,
    Real cepstrum; ADR 0151)."""
    x = np.asarray(samples)
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if x.ndim != 1 or x.shape[0] == 0:
        raise ValueError("samples must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    m = x.shape[0] if nfft is None else count(nfft, "nfft")
    if m < x.shape[0]:
        raise ValueError("nfft must be at least len(samples)")
    magnitude = np.abs(np.fft.fft(x, m))
    if np.any(magnitude == 0):
        raise ValueError("a spectrum bin is exactly 0, so its log is undefined")
    return np.asarray(np.fft.ifft(np.log(magnitude)).real, dtype=np.float64)


def minimum_phase(samples: ArrayLike, nfft: int | None = None) -> NDArray[np.float64]:
    """The minimum-phase sequence with the magnitude spectrum of ``samples``, by folding the real
    cepstrum: ``nfft`` values (conventions: Spectra, Minimum phase; ADR 0153)."""
    if nfft is None:
        x = np.asarray(samples)
        n = x.shape[0] if x.ndim == 1 else 0
        nfft = 1 << (max(64, 8 * n) - 1).bit_length()
    c = real_cepstrum(samples, nfft)
    m = c.shape[0]
    half = (m + 1) // 2
    folded = np.zeros(m)
    folded[0] = c[0]
    folded[1:half] = 2 * c[1:half]
    if m % 2 == 0:
        folded[m // 2] = c[m // 2]
    return np.asarray(np.fft.ifft(np.exp(np.fft.fft(folded))).real, dtype=np.float64)


def mel_filterbank(
    n_filters: int,
    nfft: int,
    sample_rate: float,
    min_frequency: float = 0.0,
    max_frequency: float | None = None,
    *,
    scale: str = "htk",
    area_normalized: bool = False,
) -> NDArray[np.float64]:
    """Triangular filters equally spaced in mel on the ``nfft//2 + 1`` one-sided bins, one row
    per filter (conventions: Spectra, Mel filterbank; ADR 0155)."""
    n = count(n_filters, "n_filters")
    if n < 1:
        raise ValueError("n_filters must be at least 1")
    if count(nfft, "nfft") < 2:
        raise ValueError("nfft must be at least 2")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    lo = real(min_frequency, "min_frequency")
    hi = fs / 2 if max_frequency is None else real(max_frequency, "max_frequency")
    if not (math.isfinite(lo) and math.isfinite(hi) and 0 <= lo < hi <= fs / 2):
        raise ValueError("need 0 <= min_frequency < max_frequency <= sample_rate/2")
    m_lo = float(units.hz_to_mel(lo, scale=scale))
    m_hi = float(units.hz_to_mel(hi, scale=scale))
    mels = np.array([m_lo + (m_hi - m_lo) * i / (n + 1) for i in range(n + 2)])
    f = np.asarray(units.mel_to_hz(mels, scale=scale), dtype=np.float64)
    bins = np.arange(nfft // 2 + 1) * fs / nfft
    weights = np.empty((n, bins.size))
    for i in range(n):
        rising = (bins - f[i]) / (f[i + 1] - f[i])
        falling = (f[i + 2] - bins) / (f[i + 2] - f[i + 1])
        weights[i] = np.maximum(0.0, np.minimum(rising, falling))
        if area_normalized:
            weights[i] *= 2.0 / (f[i + 2] - f[i])
    return weights


def _dct_input(values: ArrayLike, what: str) -> NDArray[np.float64]:
    x = np.asarray(values)
    if np.iscomplexobj(x):
        raise ValueError(f"{what} must be real")
    x = x.astype(np.float64, copy=False)
    if x.ndim != 1 or x.shape[0] == 0:
        raise ValueError(f"{what} must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{what} must be finite")
    return x


def _dct_matrix(n: int) -> NDArray[np.float64]:
    """``C[k, n] = cos(pi k (2n+1) / (2N))`` from one table indexed ``k(2n+1) mod 4N``."""
    table = np.cos(np.pi * np.arange(4 * n) / (2 * n))
    k = np.arange(n)
    return np.asarray(table[np.outer(k, 2 * k + 1) % (4 * n)], dtype=np.float64)


def dct(samples: ArrayLike, *, orthonormal: bool = True) -> NDArray[np.float64]:
    """DCT-II: ``X[k] = s_k sum x[n] cos(pi k (2n+1) / (2N))``, orthonormal or ``s_k = 2``
    (conventions: Spectra, DCT-II; ADR 0156)."""
    x = _dct_input(samples, "samples")
    n = x.shape[0]
    out = _dct_matrix(n) @ x
    if orthonormal:
        out[0] *= math.sqrt(1 / n)
        out[1:] *= math.sqrt(2 / n)
    else:
        out *= 2
    return np.asarray(out, dtype=np.float64)


def idct(coefficients: ArrayLike, *, orthonormal: bool = True) -> NDArray[np.float64]:
    """The exact inverse of ``dct`` with the same scaling, a DCT-III (conventions: Spectra,
    DCT-II; ADR 0156)."""
    c = _dct_input(coefficients, "coefficients").copy()
    n = c.shape[0]
    if orthonormal:
        c[0] *= math.sqrt(1 / n)
        c[1:] *= math.sqrt(2 / n)
    else:
        c[0] /= 2
        c /= n
    return np.asarray(_dct_matrix(n).T @ c, dtype=np.float64)


def find_tones(
    frequencies: ArrayLike,
    psd: ArrayLike,
    count: int,
    *,
    min_prominence: float = 0.0,
    scale: str = "db",
) -> list[Tone]:
    """The ``count`` most prominent spectral peaks, each with its frequency and height
    interpolated on ``scale``; most prominent first, ties to the lower frequency."""
    if scale not in ("db", "linear"):
        raise ValueError('scale must be "db" or "linear"')
    wanted = _checks.count(count, "count")
    if wanted < 1:
        raise ValueError("count must be at least 1")
    peaks = spectral_peaks(frequencies, psd, min_prominence=min_prominence)
    ranked = sorted(peaks, key=lambda p: -p.prominence)[:wanted]
    f = np.asarray(frequencies, dtype=np.float64)
    x = np.asarray(psd, dtype=np.float64)
    out = []
    for p in ranked:
        v = _vertex(f, x, p.index, scale)
        if v is None:
            out.append(Tone(p.index, p.frequency, p.height, p.prominence))
        else:
            out.append(Tone(p.index, v.frequency, v.height, p.prominence))
    return out


def band_energy_ratio(
    frequencies: ArrayLike,
    psd: ArrayLike,
    split: float,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> BandEnergyRatio:
    """The PSD's power above ``split`` (Hz) over its power below, the PSD taken as constant over
    each bin, over ``band = (low, high)`` in Hz (the whole spectrum by default)."""
    s = real(split, "split")
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    if not lo < s < hi:
        raise ValueError("split must be strictly inside the band")
    d = power / (right - left)
    below = np.minimum(right, s) - np.maximum(left, lo)
    above = np.minimum(right, hi) - np.maximum(left, s)
    low = float(np.sum(d * np.maximum(below, 0.0)))
    high = float(np.sum(d * np.maximum(above, 0.0)))
    if not low + high > 0:
        raise ValueError("the band has no power")
    if low == 0:
        return BandEnergyRatio(low, high, math.inf, math.inf)
    if high == 0:
        return BandEnergyRatio(low, high, 0.0, -math.inf)
    return BandEnergyRatio(low, high, high / low, 10 * math.log10(high / low))


def harmonic_to_noise(
    frequencies: ArrayLike, psd: ArrayLike, fundamental: float, half_width: float
) -> HarmonicToNoise:
    """The bin power within ``half_width`` Hz of a harmonic ``m*fundamental`` (``m >= 1``) over
    the bin power everywhere else, DC included; whole bins, never split."""
    f0 = real(fundamental, "fundamental")
    if not f0 > 0:
        raise ValueError("fundamental must be > 0")
    w = real(half_width, "half_width")
    if not 0 <= w < f0 / 2:
        raise ValueError("half_width must be >= 0 and below half the fundamental")
    power, _, _ = _bins(frequencies, psd, None)
    f = np.asarray(frequencies, dtype=np.float64)
    m = np.floor(f / f0 + 0.5)
    near = (m >= 1) & (np.abs(f - m * f0) <= w)
    harmonic = float(np.sum(power[near]))
    noise = float(np.sum(power[~near]))
    if not harmonic + noise > 0:
        raise ValueError("the spectrum has no power")
    if noise == 0:
        return HarmonicToNoise(harmonic, noise, math.inf, math.inf)
    if harmonic == 0:
        return HarmonicToNoise(harmonic, noise, 0.0, -math.inf)
    return HarmonicToNoise(harmonic, noise, harmonic / noise, 10 * math.log10(harmonic / noise))


def _fill(w: NDArray[np.float64], d: NDArray[np.float64], width: float) -> float:
    """The mean of ``d`` over the first ``width`` of the widths ``w``, in order."""
    taken = acc = 0.0
    for wi, di in zip(w, d, strict=True):
        t = min(float(wi), width - taken)
        if not t > 0:
            break
        acc += t * float(di)
        taken += t
    return acc / width


def spectral_contrast(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
    fraction: float = 0.2,
) -> SpectralContrast:
    """The mean PSD over the loudest and the quietest ``fraction`` of the band's width, and their
    ratio in dB, the PSD taken as constant over each bin, over ``band = (low, high)`` in Hz (the
    whole spectrum by default)."""
    q = real(fraction, "fraction")
    if not 0 < q <= 0.5:
        raise ValueError("fraction must be in (0, 1/2]")
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    w, d = (b - a)[keep], (power / (right - left))[keep]
    if not float(np.sum(d * w)) > 0:
        raise ValueError("the band has no power")
    width = q * float(np.sum(w))
    up = np.argsort(d, kind="stable")
    down = up[::-1]
    peak, valley = _fill(w[down], d[down], width), _fill(w[up], d[up], width)
    db = math.inf if valley == 0 else 10 * math.log10(peak / valley)
    return SpectralContrast(peak, valley, db)


def spectral_entropy(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> SpectralEntropy:
    """The differential entropy of the PSD, taken as constant over each bin and normalized to
    unit power, over ``band = (low, high)`` in Hz (the whole spectrum by default)."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    a, b, d = a[keep], b[keep], (power / (right - left))[keep]
    total = float(np.sum(d * (b - a)))
    if not total > 0:
        raise ValueError("the band has no power")
    live = d > 0
    p = d[live] / total
    h = -float(np.sum(p * (b[live] - a[live]) * np.log(p)))
    width = math.exp(h)
    return SpectralEntropy(h, width, width / (hi - lo))


def spectral_flux(
    frequencies: ArrayLike,
    previous: ArrayLike,
    current: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
    normalize: bool = True,
    rectify: bool = True,
) -> float:
    """The L2 distance between two PSD frames taken as constant over each bin, over ``band =
    (low, high)`` in Hz (the whole spectrum by default); each frame scaled to unit power with
    ``normalize``, only rises counted with ``rectify`` (conventions: Spectra, Spectral flux; ADR
    0129)."""
    frames = []
    for x in (previous, current):
        power, left, right = _bins(frequencies, x, span)
        lo, hi = _band_edges(band, left, right)
        a, b = np.maximum(left, lo), np.minimum(right, hi)
        keep = b > a
        a, b, d = a[keep], b[keep], (power / (right - left))[keep]
        if normalize:
            total = float(np.sum(d * (b - a)))
            if not total > 0:
                raise ValueError("with normalize, each frame needs power in the band")
            d = d / total
        frames.append(d)
    delta = frames[1] - frames[0]
    if rectify:
        delta = np.maximum(delta, 0.0)
    return math.sqrt(float(np.sum(delta * delta * (b - a))))


def spectral_variation(
    frequencies: ArrayLike,
    previous: ArrayLike,
    current: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> float:
    """One minus the normalized correlation of two PSD frames taken as constant over each bin,
    over ``band = (low, high)`` in Hz (the whole spectrum by default) (conventions: Spectra,
    Spectral variation; ADR 0131)."""
    frames = []
    for x in (previous, current):
        power, left, right = _bins(frequencies, x, span)
        lo, hi = _band_edges(band, left, right)
        a, b = np.maximum(left, lo), np.minimum(right, hi)
        keep = b > a
        w, d = (b - a)[keep], (power / (right - left))[keep]
        if not float(np.sum(d * w)) > 0:
            raise ValueError("each frame needs power in the band")
        frames.append(d)
    d0, d1 = frames
    cross = float(np.sum(d0 * d1 * w))
    return 1.0 - cross / math.sqrt(float(np.sum(d0 * d0 * w)) * float(np.sum(d1 * d1 * w)))


def spectral_irregularity(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> float:
    """How jagged the PSD is from bin to bin: the squared jumps between neighbouring pieces,
    each weighted by the two pieces' mean width, over the PSD's squared norm (conventions:
    Spectra, Spectral irregularity; ADR 0132)."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    w, d = (b - a)[keep], (power / (right - left))[keep]
    if d.size < 2:
        raise ValueError("the band must hold at least two bins")
    if not float(np.sum(d * w)) > 0:
        raise ValueError("the band has no power")
    jumps = float(np.sum(np.diff(d) ** 2 * (w[:-1] + w[1:]) / 2))
    return jumps / float(np.sum(d * d * w))


def spectral_flatness(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> SpectralFlatness:
    """The PSD's geometric mean over its arithmetic mean across ``band = (low, high)`` in Hz (the
    whole spectrum by default), each bin weighted by its overlap with the band."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    w = np.clip(np.minimum(right, hi) - np.maximum(left, lo), 0.0, None)
    keep = w > 0
    w, d = w[keep], (power / (right - left))[keep]
    total = float(np.sum(w))
    arith = float(np.sum(w * d)) / total
    if not arith > 0:
        raise ValueError("the band has no power")
    if np.any(d == 0):
        return SpectralFlatness(0.0, arith, 0.0, -math.inf)
    geo = math.exp(float(np.sum(w * np.log(d))) / total)
    return SpectralFlatness(geo, arith, geo / arith, 10 * (math.log10(geo) - math.log10(arith)))


def spectral_rolloff(
    frequencies: ArrayLike,
    psd: ArrayLike,
    fraction: float,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> float:
    """The frequency in Hz below which ``fraction`` of the band's power lies, the PSD taken as
    constant over each bin (conventions: Spectra, Spectral rolloff; ADR 0124)."""
    q = real(fraction, "fraction")
    if not 0 < q <= 1:
        raise ValueError("fraction must be in (0, 1]")
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    a, b = np.maximum(left, lo), np.minimum(right, hi)
    keep = b > a
    a, b, d = a[keep], b[keep], (power / (right - left))[keep]
    pieces = d * (b - a)
    total = float(np.sum(pieces))
    if not total > 0:
        raise ValueError("the band has no power")
    target = q * total
    running = 0.0
    for k in range(a.size):
        after = running + float(pieces[k])
        if after >= target:
            at = float(a[k]) + (target - running) / float(d[k])
            return min(max(at, float(a[k])), float(b[k]))
        running = after
    k = int(np.flatnonzero(pieces > 0)[-1])  # rounding left the running sum short of 1·power
    return float(b[k])


def spectral_crest(
    frequencies: ArrayLike,
    psd: ArrayLike,
    *,
    band: ArrayLike | None = None,
    span: Span | ArrayLike | None = None,
) -> SpectralCrest:
    """The PSD's peak over its mean across ``band = (low, high)`` in Hz (the whole spectrum by
    default), the mean weighted by each bin's overlap with the band."""
    power, left, right = _bins(frequencies, psd, span)
    lo, hi = _band_edges(band, left, right)
    w = np.clip(np.minimum(right, hi) - np.maximum(left, lo), 0.0, None)
    keep = w > 0
    w, d = w[keep], (power / (right - left))[keep]
    mean = float(np.sum(w * d)) / float(np.sum(w))
    if not mean > 0:
        raise ValueError("the band has no power")
    peak = float(np.max(d))
    return SpectralCrest(peak, mean, peak / mean, 10 * (math.log10(peak) - math.log10(mean)))


@dataclass(frozen=True)
class DbBandwidth:
    """Where the PSD falls ``drop_db`` below its peak (conventions: Spectra, x dB bandwidth; ADR
    0122). Frequencies are in the PSD's axis."""

    peak_frequency: float
    peak_psd: float
    lower: float
    upper: float
    bandwidth: float


def db_bandwidth(
    frequencies: ArrayLike, psd: ArrayLike, drop_db: float, *, band: ArrayLike | None = None
) -> DbBandwidth:
    """The span between the first points either side of the peak where the PSD has fallen
    ``drop_db`` below it, interpolated linearly in power between bins."""
    drop = real(drop_db, "drop_db")
    if not drop > 0:
        raise ValueError("drop_db must be positive")
    _bins(frequencies, psd, None)
    f = np.asarray(frequencies, dtype=np.float64)
    p = np.asarray(psd, dtype=np.float64)
    if band is None:
        idx = np.arange(f.size)
    else:
        b = np.asarray(band, dtype=np.float64)
        if b.shape != (2,) or not np.all(np.isfinite(b)):
            raise ValueError("band must be (low, high) with finite edges")
        if not b[0] < b[1]:
            raise ValueError("band low must be below band high")
        idx = np.flatnonzero((f >= b[0]) & (f <= b[1]))
        if idx.size == 0:
            raise ValueError("no bin lies in the band")
    first, last = int(idx[0]), int(idx[-1])
    k = first + int(np.argmax(p[first : last + 1]))
    peak = float(p[k])
    if not peak > 0:
        raise ValueError("the band has no power")
    t = peak * 10.0 ** (-drop / 10)
    delta = float(f[-1] - f[0]) / (f.size - 1)

    def edge(step: int) -> float:
        i = k + step
        while first <= i <= last:
            if p[i] <= t:
                j = i - step  # the neighbour towards the peak, above t
                frac = (t - p[i]) / (p[j] - p[i])
                return float(f[i] - step * frac * delta)
            i += step
        raise ValueError(f"the PSD does not fall {drop} dB below the peak within the band")

    lower, upper = edge(-1), edge(+1)
    return DbBandwidth(float(f[k]), peak, lower, upper, upper - lower)


def acpr_rrc(
    frequencies: ArrayLike,
    psd: ArrayLike,
    center: float,
    symbol_rate: float,
    alpha: float,
    offsets: ArrayLike,
    *,
    span: Span | ArrayLike | None = None,
) -> Acpr:
    """ACPR with every channel weighted by a root-raised-cosine filter's ``|H(f)|^2`` (peak 1,
    roll-off ``alpha``, at ``symbol_rate``), each bin's power weighted at its center
    (conventions: Spectra, ACPR; ADR 0111)."""
    c = real(center, "center")
    rs = real(symbol_rate, "symbol_rate")
    a = real(alpha, "alpha")
    if not rs > 0:
        raise ValueError("symbol_rate must be positive")
    if not 0 < a <= 1:
        raise ValueError("alpha must be in (0, 1]")
    o = np.asarray(offsets, dtype=np.float64)
    if o.ndim != 1 or o.size == 0 or not np.all(np.isfinite(o) & (o > 0)):
        raise ValueError("offsets must be a non-empty list of finite values > 0")
    power, left, right = _bins(frequencies, psd, span)
    f = np.asarray(frequencies, dtype=np.float64)
    slack = 1e-9 * float(np.max(right - left))  # rounding in center +- offset +- support
    flat, edge = (1 - a) * rs / 2, (1 + a) * rs / 2

    def channel(at: float) -> float:
        if at - edge < left[0] - slack or at + edge > right[-1] + slack:
            raise ValueError(
                f"channel [{at - edge}, {at + edge}] leaves the spectrum [{left[0]}, {right[-1]}]"
            )
        x = np.abs(f - at)
        taper = 0.5 * (1 + np.cos(np.pi * (x - flat) / (a * rs)))
        g = np.where(x <= flat, 1.0, np.where(x < edge, taper, 0.0))
        return float(np.sum(power * g))

    main = channel(c)
    if not main > 0:
        raise ValueError("the main channel has no power")
    lower = np.array([channel(c - v) for v in o])
    upper = np.array([channel(c + v) for v in o])
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
