"""Power measurements and tone metrics. Definitions in docs/conventions.md."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from . import dsp, spectral, units
from ._checks import count, real


@dataclass(frozen=True)
class PowerStats:
    """Power statistics of a sample sequence, in sample units (squared for powers).

    ``dc`` is the mean sample (complex for complex input). ``peak_index`` is the first sample with
    the largest ``|x|^2``. ``papr_db`` is ``10*log10(peak_power / mean_power)``; NaN when the mean
    power is zero.
    """

    num_samples: int
    mean_power: float
    rms: float
    peak_power: float
    peak_amplitude: float
    peak_index: int
    papr_db: float
    dc: complex


def power_stats(samples: ArrayLike) -> PowerStats:
    """Mean power, RMS, peak, PAPR and DC of ``samples`` (real or complex, at least one sample)."""
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] == 0:
        raise ValueError("samples must be a non-empty one-dimensional array")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    p = x.real * x.real + x.imag * x.imag if np.iscomplexobj(x) else x * x
    mean_power = float(np.mean(p))
    peak_index = int(np.argmax(p))
    peak_power = float(p[peak_index])
    papr_db = 10.0 * float(np.log10(peak_power / mean_power)) if mean_power > 0 else float("nan")
    return PowerStats(
        num_samples=int(x.shape[0]),
        mean_power=mean_power,
        rms=float(np.sqrt(mean_power)),
        peak_power=peak_power,
        peak_amplitude=float(np.sqrt(peak_power)),
        peak_index=peak_index,
        papr_db=papr_db,
        dc=complex(np.mean(x)),
    )


@dataclass(frozen=True)
class AutocorrelationPitch:
    """The fundamental from the highest autocorrelation peak: the frequency in Hz, the refined
    lag in samples and the voicing ``r[L]/r[0]`` (conventions: Autocorrelation pitch;
    ADR 0150)."""

    frequency: float
    lag: float
    voicing: float


@dataclass(frozen=True)
class CepstrumPitch:
    """The fundamental from the highest real-cepstrum peak: the frequency in Hz, the refined
    quefrency in samples and the strength ``c[L]`` (conventions: Cepstrum pitch; ADR 0152)."""

    frequency: float
    quefrency: float
    strength: float


@dataclass(frozen=True, eq=False)
class AllanDeviation:
    """Overlapping Allan deviations at averaging times ``taus`` in seconds (conventions: Allan
    deviation; ADR 0327)."""

    taus: NDArray[np.float64]
    deviations: NDArray[np.float64]


@dataclass(frozen=True, eq=False)
class DetrendedFluctuation:
    """DFA-1 fluctuations at each box size and their scaling exponent (conventions: Detrended
    fluctuation analysis; ADR 0332)."""

    scales: NDArray[np.int64]
    fluctuations: NDArray[np.float64]
    alpha: float


@dataclass(frozen=True, eq=False)
class Mtie:
    """Maximum time interval errors in seconds at observation intervals ``taus`` in seconds
    (conventions: Maximum time interval error; ADR 0337)."""

    taus: NDArray[np.float64]
    values: NDArray[np.float64]


@dataclass(frozen=True, eq=False)
class RescaledRange:
    """Mean rescaled ranges at each box size and the Hurst exponent they give (conventions:
    Rescaled range; ADR 0340)."""

    scales: NDArray[np.int64]
    values: NDArray[np.float64]
    hurst: float


@dataclass(frozen=True)
class CorrelationSum:
    """The correlation sum at each radius and the correlation dimension it gives (conventions:
    Correlation sum; ADR 0349)."""

    radii: NDArray[np.float64]
    values: NDArray[np.float64]
    dimension: float


@dataclass(frozen=True)
class RecurrenceQuantification:
    """The recurrence rate, determinism and longest diagonal line of a recurrence plot
    (conventions: Recurrence quantification; ADR 0350)."""

    rate: float
    determinism: float
    longest: int


@dataclass(frozen=True)
class HjorthParameters:
    """Hjorth's activity, mobility and complexity (conventions: Hjorth parameters; ADR 0324).
    Mobility is in radians per sample."""

    activity: float
    mobility: float
    complexity: float


@dataclass(frozen=True)
class TemporalCentroid:
    """The energy-weighted mean time of a signal and its spread about it, both in seconds
    (conventions: Temporal centroid; ADR 0147)."""

    centroid: float
    spread: float


@dataclass(frozen=True, eq=False)
class PowerCcdf:
    """Fraction of samples whose instantaneous power exceeds the mean by each level (conventions:
    Power CCDF; ADR 0119)."""

    mean_power: float
    levels_db: NDArray[np.float64]
    probabilities: NDArray[np.float64]


@dataclass(frozen=True, eq=False)
class EnergySeparation:
    """DESA-2 instantaneous amplitude and frequency in Hz for ``n = 2 .. N-3`` (conventions:
    Energy separation; ADR 0189)."""

    amplitude: NDArray[np.float64]
    frequency: NDArray[np.float64]


@dataclass(frozen=True)
class GccPhat:
    """GCC-PHAT delay of ``x`` relative to ``y`` (conventions: GCC-PHAT delay; ADR 0191)."""

    delay: float
    lag: int
    peak: float


def _instantaneous_power(samples: ArrayLike) -> tuple[NDArray[np.float64], float]:
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] == 0:
        raise ValueError("samples must be a non-empty one-dimensional array")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    p = x.real * x.real + x.imag * x.imag if np.iscomplexobj(x) else x * x
    mean = float(np.mean(p))
    if not mean > 0:
        raise ValueError("the mean power must be positive")
    return np.asarray(p, dtype=np.float64), mean


def zero_crossing_rate(samples: ArrayLike) -> float:
    """The fraction of adjacent sample pairs whose signs differ, a sample being positive when
    ``x >= 0`` (conventions: Zero-crossing rate; ADR 0146)."""
    x = np.asarray(samples)
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if x.ndim != 1 or x.shape[0] < 2:
        raise ValueError("samples must be a one-dimensional array of at least two samples")
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    positive = x >= 0
    return int(np.count_nonzero(positive[1:] != positive[:-1])) / int(x.shape[0] - 1)


def allan_deviation(
    fractional_frequency: ArrayLike, sample_interval: float, averaging_factors: Sequence[int]
) -> AllanDeviation:
    """The overlapping Allan deviation of fractional-frequency samples at ``tau = m *
    sample_interval`` for each averaging factor ``m`` (conventions: Allan deviation; ADR 0327)."""
    tau0 = real(sample_interval, "sample_interval")
    if not tau0 > 0:
        raise ValueError("sample_interval must be positive")
    y = np.asarray(fractional_frequency)
    if y.ndim != 1 or y.shape[0] < 2:
        raise ValueError("fractional_frequency must be a one-dimensional array of at least 2")
    if np.iscomplexobj(y):
        raise ValueError("fractional_frequency must be real")
    y = y.astype(np.float64, copy=False)
    if not np.all(np.isfinite(y)):
        raise ValueError("fractional_frequency must be finite")
    factors = [count(m, "averaging_factors") for m in averaging_factors]
    if not factors:
        raise ValueError("averaging_factors must not be empty")
    size = y.shape[0]
    if any(m < 1 or 2 * m > size for m in factors):
        raise ValueError("each averaging factor m must be at least 1 with 2 m <= len")
    deviations = np.empty(len(factors))
    for i, m in enumerate(factors):
        means = np.lib.stride_tricks.sliding_window_view(y, m).mean(axis=1)
        d = means[m:] - means[: size - 2 * m + 1]
        deviations[i] = math.sqrt(float(np.sum(d * d)) / (2 * (size - 2 * m + 1)))
    taus = np.array(factors, dtype=np.float64) * tau0
    return AllanDeviation(taus, deviations)


def modified_allan_deviation(
    fractional_frequency: ArrayLike, sample_interval: float, averaging_factors: Sequence[int]
) -> AllanDeviation:
    """The modified Allan deviation of fractional-frequency samples at ``tau = m *
    sample_interval`` for each averaging factor ``m`` (conventions: Modified Allan deviation;
    ADR 0328)."""
    tau0 = real(sample_interval, "sample_interval")
    if not tau0 > 0:
        raise ValueError("sample_interval must be positive")
    y = np.asarray(fractional_frequency)
    if y.ndim != 1 or y.shape[0] < 2:
        raise ValueError("fractional_frequency must be a one-dimensional array of at least 2")
    if np.iscomplexobj(y):
        raise ValueError("fractional_frequency must be real")
    y = y.astype(np.float64, copy=False)
    if not np.all(np.isfinite(y)):
        raise ValueError("fractional_frequency must be finite")
    factors = [count(m, "averaging_factors") for m in averaging_factors]
    if not factors:
        raise ValueError("averaging_factors must not be empty")
    size = y.shape[0]
    if any(m < 1 or 3 * m > size + 1 for m in factors):
        raise ValueError("each averaging factor m must be at least 1 with 3 m <= len + 1")
    deviations = np.empty(len(factors))
    view = np.lib.stride_tricks.sliding_window_view
    for i, m in enumerate(factors):
        means = view(y, m).mean(axis=1)
        d = means[m:] - means[: size - 2 * m + 1]
        s = view(d, m).sum(axis=1)
        deviations[i] = math.sqrt(float(np.sum(s * s)) / (2 * m * m * (size - 3 * m + 2)))
    taus = np.array(factors, dtype=np.float64) * tau0
    return AllanDeviation(taus, deviations)


def hadamard_deviation(
    fractional_frequency: ArrayLike, sample_interval: float, averaging_factors: Sequence[int]
) -> AllanDeviation:
    """The overlapping Hadamard deviation of fractional-frequency samples at ``tau = m *
    sample_interval`` for each averaging factor ``m`` (conventions: Hadamard deviation;
    ADR 0329)."""
    tau0 = real(sample_interval, "sample_interval")
    if not tau0 > 0:
        raise ValueError("sample_interval must be positive")
    y = np.asarray(fractional_frequency)
    if y.ndim != 1 or y.shape[0] < 3:
        raise ValueError("fractional_frequency must be a one-dimensional array of at least 3")
    if np.iscomplexobj(y):
        raise ValueError("fractional_frequency must be real")
    y = y.astype(np.float64, copy=False)
    if not np.all(np.isfinite(y)):
        raise ValueError("fractional_frequency must be finite")
    factors = [count(m, "averaging_factors") for m in averaging_factors]
    if not factors:
        raise ValueError("averaging_factors must not be empty")
    size = y.shape[0]
    if any(m < 1 or 3 * m > size for m in factors):
        raise ValueError("each averaging factor m must be at least 1 with 3 m <= len")
    deviations = np.empty(len(factors))
    for i, m in enumerate(factors):
        means = np.lib.stride_tricks.sliding_window_view(y, m).mean(axis=1)
        terms = size - 3 * m + 1
        d = (means[2 * m :] - means[m : m + terms]) - (means[m : m + terms] - means[:terms])
        deviations[i] = math.sqrt(float(np.sum(d * d)) / (6 * terms))
    taus = np.array(factors, dtype=np.float64) * tau0
    return AllanDeviation(taus, deviations)


def higuchi_dimension(samples: ArrayLike, k_max: int) -> float:
    """Higuchi's fractal dimension: the least-squares slope of ``ln L(k)`` against ``ln(1/k)``
    for ``k = 1 .. k_max`` (conventions: Higuchi fractal dimension; ADR 0330)."""
    kmax = count(k_max, "k_max")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    size = x.shape[0]
    if kmax < 2 or 2 * kmax > size:
        raise ValueError("k_max must be at least 2 with 2 k_max <= len(samples)")
    lengths = np.empty(kmax)
    for k in range(1, kmax + 1):
        total = 0.0
        for m in range(k):
            sub = x[m::k]
            steps = sub.shape[0] - 1
            total += float(np.sum(np.abs(np.diff(sub)))) * (size - 1) / (steps * k) / k
        lengths[k - 1] = total / k
    if not np.all(lengths > 0):
        raise ValueError("the curve must have a length at every k")
    lx = -np.log(np.arange(1, kmax + 1, dtype=np.float64))
    ly = np.log(lengths)
    dx = lx - lx.mean()
    return float(np.sum(dx * (ly - ly.mean())) / np.sum(dx * dx))


def time_deviation(
    fractional_frequency: ArrayLike, sample_interval: float, averaging_factors: Sequence[int]
) -> AllanDeviation:
    """The time deviation ``(tau / sqrt 3) MDEV(tau)`` in seconds for each averaging factor
    (conventions: Time deviation; ADR 0331)."""
    mod = modified_allan_deviation(fractional_frequency, sample_interval, averaging_factors)
    deviations: NDArray[np.float64] = mod.taus / math.sqrt(3) * mod.deviations
    return AllanDeviation(mod.taus, deviations)


def detrended_fluctuation(samples: ArrayLike, scales: Sequence[int]) -> DetrendedFluctuation:
    """Detrended fluctuation analysis, DFA-1: the RMS of the linearly detrended profile in
    boxes of each size, and the log-log slope ``alpha`` (conventions: Detrended fluctuation
    analysis; ADR 0332)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    sizes = [count(s, "scales") for s in scales]
    size = x.shape[0]
    if len(sizes) < 2:
        raise ValueError("scales must have at least two entries")
    if any(sizes[i + 1] <= sizes[i] for i in range(len(sizes) - 1)):
        raise ValueError("scales must be strictly increasing")
    if sizes[0] < 4 or sizes[-1] > size:
        raise ValueError("each scale must be at least 4 and at most len(samples)")
    profile = np.cumsum(x - x.mean())
    fluctuations = np.empty(len(sizes))
    for i, s in enumerate(sizes):
        boxes = size // s
        y = profile[: boxes * s].reshape(boxes, s)
        t = np.arange(s, dtype=np.float64) - (s - 1) / 2
        yc = y - y.mean(axis=1, keepdims=True)
        slope = (yc @ t) / float(t @ t)
        r = yc - slope[:, None] * t
        fluctuations[i] = math.sqrt(float(np.sum(r * r)) / (boxes * s))
    if not np.all(fluctuations > 0):
        raise ValueError("the detrended profile must fluctuate at every scale")
    lx = np.log(np.array(sizes, dtype=np.float64))
    ly = np.log(fluctuations)
    dx = lx - lx.mean()
    alpha = float(np.sum(dx * (ly - ly.mean())) / np.sum(dx * dx))
    return DetrendedFluctuation(np.array(sizes, dtype=np.int64), fluctuations, alpha)


def approximate_entropy(samples: ArrayLike, m: int, r: float) -> float:
    """Pincus's approximate entropy ``Phi_m - Phi_{m+1}``, self-matches counted, Chebyshev
    distance (conventions: Approximate entropy; ADR 0333)."""
    k = count(m, "m")
    if k < 1:
        raise ValueError("m must be at least 1")
    tol = real(r, "r")
    if tol < 0:
        raise ValueError("r must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if x.shape[0] < k + 2:
        raise ValueError("samples must be at least m + 2 long")

    def phi(length: int) -> float:
        t = np.lib.stride_tricks.sliding_window_view(x, length)
        n = t.shape[0]
        counts = np.array(
            [np.count_nonzero(np.max(np.abs(t - t[i]), axis=1) <= tol) for i in range(n)]
        )
        return float(np.mean(np.log(counts / n)))

    return phi(k) - phi(k + 1)


def _at_least_three_real(samples: ArrayLike) -> NDArray[np.float64]:
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] < 3:
        raise ValueError("samples must be a one-dimensional array of at least 3")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    return x


def katz_dimension(samples: ArrayLike) -> float:
    """Katz's fractal dimension ``log10 n / (log10 n + log10(d / L))`` of the points
    ``(i, x[i])`` (conventions: Katz fractal dimension; ADR 0334)."""
    x = _at_least_three_real(samples)
    n = x.shape[0] - 1
    length = float(np.sum(np.hypot(1.0, np.diff(x))))
    extent = float(np.max(np.hypot(np.arange(n + 1, dtype=np.float64), x - x[0])))
    denominator = math.log10(n) + math.log10(extent / length)
    if not denominator > 0:
        raise ValueError("n d must exceed L for the Katz dimension to be defined")
    return math.log10(n) / denominator


def petrosian_dimension(samples: ArrayLike) -> float:
    """Petrosian's fractal dimension ``log10 n / (log10 n + log10(n / (n + 0.4 N_delta)))``
    with ``N_delta`` the sign changes of the first difference (conventions: Petrosian fractal
    dimension; ADR 0335)."""
    x = _at_least_three_real(samples)
    n = x.shape[0]
    s = np.sign(np.diff(x))
    changes = int(np.count_nonzero(s[:-1] * s[1:] < 0))
    return math.log10(n) / (math.log10(n) + math.log10(n / (n + 0.4 * changes)))


def lempel_ziv_complexity(bits: ArrayLike) -> int:
    """The LZ76 phrase count of a 0/1 sequence, by the Kaspar-Schuster scan (conventions:
    Lempel-Ziv complexity; ADR 0336)."""
    b = np.asarray(bits)
    if b.ndim != 1 or b.shape[0] < 1:
        raise ValueError("bits must be a one-dimensional array of at least 1")
    if not np.all((b == 0) | (b == 1)):
        raise ValueError("bits must be 0 or 1")
    s = b.astype(np.uint8).tolist()
    n = len(s)
    if n == 1:
        return 1
    i, k, start, k_max, phrases = 0, 1, 1, 1, 1
    while True:
        if s[i + k - 1] == s[start + k - 1]:
            k += 1
            if start + k > n:
                return phrases + 1
        else:
            k_max = max(k_max, k)
            i += 1
            if i == start:
                phrases += 1
                start += k_max
                if start + 1 > n:
                    return phrases
                i, k, k_max = 0, 1, 1
            else:
                k = 1


def mtie(time_error: ArrayLike, sample_interval: float, window_sizes: Sequence[int]) -> Mtie:
    """The maximum time interval error: the largest peak-to-peak time error over every window
    of ``n + 1`` samples, at ``tau = n * sample_interval`` (conventions: Maximum time interval
    error; ADR 0337)."""
    tau0 = real(sample_interval, "sample_interval")
    if not tau0 > 0:
        raise ValueError("sample_interval must be positive")
    x = np.asarray(time_error)
    if x.ndim != 1 or x.shape[0] < 2:
        raise ValueError("time_error must be a one-dimensional array of at least 2")
    if np.iscomplexobj(x):
        raise ValueError("time_error must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("time_error must be finite")
    sizes = [count(n, "window_sizes") for n in window_sizes]
    if not sizes:
        raise ValueError("window_sizes must not be empty")
    if any(n < 1 or n > x.shape[0] - 1 for n in sizes):
        raise ValueError("each window size n must be from 1 to len(time_error) - 1")
    values = np.empty(len(sizes))
    for i, n in enumerate(sizes):
        w = np.lib.stride_tricks.sliding_window_view(x, n + 1)
        values[i] = float(np.max(w.max(axis=1) - w.min(axis=1)))
    return Mtie(np.array(sizes, dtype=np.float64) * tau0, values)


def multiscale_entropy(
    samples: ArrayLike, m: int, r: float, scales: Sequence[int]
) -> NDArray[np.float64]:
    """Costa's multiscale entropy: the sample entropy of the non-overlapping coarse-grained
    means at each scale, ``r`` the same at every scale (conventions: Multiscale entropy;
    ADR 0338)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    k = count(m, "m")
    sizes = [count(s, "scales") for s in scales]
    if not sizes:
        raise ValueError("scales must not be empty")
    if any(s < 1 or x.shape[0] // s < k + 2 for s in sizes):
        raise ValueError("each scale must be at least 1 with len(samples) // scale >= m + 2")
    out = np.empty(len(sizes))
    for i, s in enumerate(sizes):
        boxes = x.shape[0] // s
        coarse = x[: boxes * s].reshape(boxes, s).sum(axis=1) / s
        out[i] = sample_entropy(coarse, k, r)
    return out


def fuzzy_entropy(samples: ArrayLike, m: int, r: float, n: float = 2) -> float:
    """Chen's fuzzy entropy ``ln phi_m - ln phi_{m+1}``: baseline-removed templates, Chebyshev
    distance and the membership ``exp(-d**n / r)`` (conventions: Fuzzy entropy; ADR 0339)."""
    k = count(m, "m")
    if k < 1:
        raise ValueError("m must be at least 1")
    width = real(r, "r")
    if not width > 0:
        raise ValueError("r must be positive")
    power = real(n, "n")
    if not power >= 1:
        raise ValueError("n must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    starts = x.shape[0] - k
    if starts < 2:
        raise ValueError("samples must be at least m + 2 long")

    def phi(length: int) -> float:
        t = np.lib.stride_tricks.sliding_window_view(x, length)[:starts]
        t = t - t.mean(axis=1, keepdims=True)
        total = 0.0
        for i in range(starts):
            d = np.max(np.abs(t - t[i]), axis=1)
            total += float(np.sum(np.exp(-(d**power) / width))) - 1.0
        return float(total / (starts * (starts - 1)))

    a, b = phi(k), phi(k + 1)
    if not (a > 0 and b > 0):
        raise ValueError("the memberships underflowed to 0")
    return math.log(a) - math.log(b)


def rescaled_range(samples: ArrayLike, scales: Sequence[int]) -> RescaledRange:
    """Hurst's rescaled-range analysis: the mean ``R/S`` over non-overlapping boxes of each
    size, and the least-squares slope of its logarithm against ``ln s`` (conventions:
    Rescaled range; ADR 0340)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    sizes = [count(s, "scales") for s in scales]
    if len(sizes) < 2:
        raise ValueError("scales must have at least two entries")
    if any(sizes[i + 1] <= sizes[i] for i in range(len(sizes) - 1)):
        raise ValueError("scales must be strictly increasing")
    if sizes[0] < 4 or sizes[-1] > x.shape[0]:
        raise ValueError("each scale must be at least 4 and at most len(samples)")
    values = np.empty(len(sizes))
    for i, s in enumerate(sizes):
        boxes = x.shape[0] // s
        y = x[: boxes * s].reshape(boxes, s)
        y = y - y.mean(axis=1, keepdims=True)
        z = np.cumsum(y, axis=1)
        spread = np.sqrt(np.mean(y * y, axis=1))
        if not np.all(spread > 0):
            raise ValueError("every box must vary")
        values[i] = float(np.mean((z.max(axis=1) - z.min(axis=1)) / spread))
    lx = np.log(np.array(sizes, dtype=np.float64))
    ly = np.log(values)
    dx = lx - lx.mean()
    hurst = float(np.sum(dx * (ly - ly.mean())) / np.sum(dx * dx))
    return RescaledRange(np.array(sizes, dtype=np.int64), values, hurst)


def dispersion_entropy(samples: ArrayLike, m: int, classes: int, delay: int = 1) -> float:
    """Rostaghi and Azami's dispersion entropy: normal-CDF classes, then the Shannon entropy of
    the class patterns over ``ln(classes**m)`` (conventions: Dispersion entropy; ADR 0341)."""
    k = count(m, "m")
    c = count(classes, "classes")
    tau = count(delay, "delay")
    if not 1 <= k <= 10:
        raise ValueError("m must be from 1 to 10")
    if not 2 <= c <= 64:
        raise ValueError("classes must be from 2 to 64")
    if tau < 1:
        raise ValueError("delay must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    windows = x.shape[0] - (k - 1) * tau
    if windows < 1:
        raise ValueError("samples are too short for one pattern")
    sigma = float(np.std(x))
    if not sigma > 0:
        raise ValueError("samples must not be constant")
    mu = float(np.mean(x))
    scale = sigma * math.sqrt(2)
    y = np.array([0.5 * math.erfc(-(v - mu) / scale) for v in x.tolist()])
    z = np.minimum(c, np.floor(c * y).astype(np.int64) + 1)
    idx = np.arange(windows)[:, None] + tau * np.arange(k)[None, :]
    _, counts = np.unique(z[idx], axis=0, return_counts=True)
    p = counts / windows
    return float(-np.sum(p * np.log(p)) / (k * math.log(c)))


def svd_entropy(samples: ArrayLike, order: int, delay: int = 1) -> float:
    """The Shannon entropy of the normalized singular values of the delay-embedding matrix,
    over ``ln(order)`` (conventions: SVD entropy; ADR 0342)."""
    m = count(order, "order")
    tau = count(delay, "delay")
    if not 2 <= m <= 32:
        raise ValueError("order must be from 2 to 32")
    if tau < 1:
        raise ValueError("delay must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    rows = x.shape[0] - (m - 1) * tau
    if rows < m:
        raise ValueError("samples are too short: need len(samples) - (order - 1)*delay >= order")
    if not np.any(x != 0):
        raise ValueError("samples must not all be 0")
    idx = np.arange(rows)[:, None] + tau * np.arange(m)[None, :]
    s = np.linalg.svd(x[idx], compute_uv=False)
    p = s / np.sum(s)
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)) / math.log(m))


def weighted_permutation_entropy(samples: ArrayLike, order: int, delay: int = 1) -> float:
    """Permutation entropy with each window weighted by its population variance, over
    ``ln(order!)`` (conventions: Weighted permutation entropy; ADR 0343)."""
    m = count(order, "order")
    tau = count(delay, "delay")
    if not 2 <= m <= 8:
        raise ValueError("order must be from 2 to 8")
    if tau < 1:
        raise ValueError("delay must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    windows = x.shape[0] - (m - 1) * tau
    if windows < 1:
        raise ValueError("samples are too short for one window")
    idx = np.arange(windows)[:, None] + tau * np.arange(m)[None, :]
    w = x[idx]
    weights = np.var(w, axis=1)
    total = float(np.sum(weights))
    if not total > 0:
        raise ValueError("at least one window must vary")
    patterns = np.argsort(w, axis=1, kind="stable")
    _, inverse = np.unique(patterns, axis=0, return_inverse=True)
    p = np.bincount(inverse.reshape(-1), weights=weights) / total
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)) / math.log(math.factorial(m)))


def increment_entropy(samples: ArrayLike, m: int, levels: int) -> float:
    """The Shannon entropy in nats of words of ``m`` increment letters, each the sign and the
    quantized size of a step (conventions: Increment entropy; ADR 0344)."""
    k = count(m, "m")
    r = count(levels, "levels")
    if k < 1:
        raise ValueError("m must be at least 1")
    if not 1 <= r <= 1000:
        raise ValueError("levels must be from 1 to 1000")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    words = x.shape[0] - k
    if words < 1:
        raise ValueError("samples must be at least m + 1 long")
    v = np.diff(x)
    sigma = float(np.std(v))
    if not sigma > 0:
        raise ValueError("the increments must not all be 0")
    size = np.minimum(r, np.floor(np.abs(v) * r / sigma)).astype(np.int64)
    letters = (np.sign(v).astype(np.int64) + 1) * (r + 1) + size
    idx = np.arange(words)[:, None] + np.arange(k)[None, :]
    _, counts = np.unique(letters[idx], axis=0, return_counts=True)
    p = counts / words
    return float(-np.sum(p * np.log(p)))


def bubble_entropy(samples: ArrayLike, m: int) -> float:
    """Manis et al.'s bubble entropy: Renyi-2 entropies of the bubble-sort swap counts of
    windows of ``m`` and ``m + 1`` samples (conventions: Bubble entropy; ADR 0345)."""
    k = count(m, "m")
    if not 2 <= k <= 64:
        raise ValueError("m must be from 2 to 64")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if x.shape[0] < k + 1:
        raise ValueError("samples must be at least m + 1 long")

    def renyi(length: int) -> float:
        w = np.lib.stride_tricks.sliding_window_view(x, length)
        swaps = np.zeros(w.shape[0], dtype=np.int64)
        for j in range(length - 1):
            swaps += np.sum(w[:, j : j + 1] > w[:, j + 1 :], axis=1)
        counts = np.bincount(swaps)
        p = counts / w.shape[0]
        return -math.log(float(np.sum(p * p)))

    return (renyi(k + 1) - renyi(k)) / math.log((k + 1) / (k - 1))


def attention_entropy(samples: ArrayLike) -> float:
    """The mean Shannon entropy, in nats, of the four kinds of interval between strict local
    maxima and minima (conventions: Attention entropy; ADR 0346)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    mid, left, right = x[1:-1], x[:-2], x[2:]
    peaks = np.flatnonzero((mid > left) & (mid > right)) + 1
    troughs = np.flatnonzero((mid < left) & (mid < right)) + 1

    def following(a: NDArray[np.intp], b: NDArray[np.intp]) -> NDArray[np.intp]:
        j = np.searchsorted(b, a, side="right")
        keep = j < b.shape[0]
        return np.asarray(b[j[keep]] - a[keep])

    sets = [np.diff(peaks), np.diff(troughs), following(peaks, troughs), following(troughs, peaks)]
    total = 0.0
    for gaps in sets:
        if gaps.shape[0] == 0:
            raise ValueError("one of the four interval sets is empty")
        _, counts = np.unique(gaps, return_counts=True)
        p = counts / gaps.shape[0]
        total += float(-np.sum(p * np.log(p)))
    return total / 4


def slope_entropy(samples: ArrayLike, m: int, gamma: float = 1.0, delta: float = 1e-3) -> float:
    """Cuesta-Frau's slope entropy: each step of a window as one of five symbols by the
    thresholds ``gamma`` and ``delta``, then the Shannon entropy in nats of the patterns
    (conventions: Slope entropy; ADR 0347)."""
    k = count(m, "m")
    if not 2 <= k <= 16:
        raise ValueError("m must be from 2 to 16")
    g = real(gamma, "gamma")
    d0 = real(delta, "delta")
    if not 0 <= d0 < g:
        raise ValueError("need 0 <= delta < gamma")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    windows = x.shape[0] - k + 1
    if windows < 1:
        raise ValueError("samples must be at least m long")
    d = np.diff(x)
    symbols = np.zeros(d.shape[0], dtype=np.int64)
    symbols[d > d0] = 1
    symbols[d > g] = 2
    symbols[d < -d0] = -1
    symbols[d < -g] = -2
    idx = np.arange(windows)[:, None] + np.arange(k - 1)[None, :]
    _, counts = np.unique(symbols[idx], axis=0, return_counts=True)
    p = counts / windows
    return float(-np.sum(p * np.log(p)))


def distribution_entropy(samples: ArrayLike, m: int, bins: int = 512) -> float:
    """Li et al.'s distribution entropy: the Shannon entropy of the histogram of Chebyshev
    distances between windows, over ``ln(bins)`` (conventions: Distribution entropy;
    ADR 0348)."""
    k = count(m, "m")
    nb = count(bins, "bins")
    if k < 1:
        raise ValueError("m must be at least 1")
    if not 2 <= nb <= 1_000_000:
        raise ValueError("bins must be from 2 to 1000000")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    windows = x.shape[0] - k + 1
    if windows < 2:
        raise ValueError("samples must be at least m + 1 long")
    w = np.lib.stride_tricks.sliding_window_view(x, k)
    d = np.concatenate([np.max(np.abs(w[i + 1 :] - w[i]), axis=1) for i in range(windows - 1)])
    lo, hi = float(np.min(d)), float(np.max(d))
    if not hi > lo:
        return 0.0
    b = np.minimum(nb - 1, np.floor((d - lo) * nb / (hi - lo)).astype(np.int64))
    p = np.bincount(b) / d.shape[0]
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)) / math.log(nb))


def correlation_sum(
    samples: ArrayLike, m: int, radii: ArrayLike, delay: int = 1, theiler: int = 0
) -> CorrelationSum:
    """Grassberger and Procaccia's correlation sum: the share of embedded pairs closer than
    each radius in the Chebyshev distance, and the least-squares slope of its logarithm
    against ``ln r`` (conventions: Correlation sum; ADR 0349)."""
    k = count(m, "m")
    tau = count(delay, "delay")
    w = count(theiler, "theiler")
    if k < 1 or tau < 1:
        raise ValueError("m and delay must be at least 1")
    if w < 0:
        raise ValueError("theiler must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    r = np.asarray(radii)
    if r.ndim != 1 or np.iscomplexobj(r):
        raise ValueError("radii must be real and one-dimensional")
    r = r.astype(np.float64, copy=False)
    if r.shape[0] < 2:
        raise ValueError("radii must have at least two entries")
    if not (np.all(np.isfinite(r)) and r[0] > 0 and np.all(np.diff(r) > 0)):
        raise ValueError("radii must be finite, positive and strictly increasing")
    windows = x.shape[0] - (k - 1) * tau
    if windows - w < 2:
        raise ValueError("there must be at least one pair")
    emb = x[np.arange(windows)[:, None] + tau * np.arange(k)[None, :]]
    d = np.sort(
        np.concatenate([np.max(np.abs(emb[s:] - emb[:-s]), axis=1) for s in range(w + 1, windows)])
    )
    values = np.searchsorted(d, r, side="left") / d.shape[0]
    if not np.all(values > 0):
        raise ValueError("every radius must have a pair closer than it")
    lx = np.log(r)
    ly = np.log(values)
    dx = lx - lx.mean()
    dimension = float(np.sum(dx * (ly - ly.mean())) / np.sum(dx * dx))
    return CorrelationSum(r.copy(), values, dimension)


def recurrence_quantification(
    samples: ArrayLike,
    m: int,
    radius: float,
    delay: int = 1,
    min_line: int = 2,
    theiler: int = 0,
) -> RecurrenceQuantification:
    """Zbilut and Webber's recurrence quantification: the recurrence rate, determinism and
    longest diagonal line of the Chebyshev recurrence plot (conventions: Recurrence
    quantification; ADR 0350)."""
    k = count(m, "m")
    tau = count(delay, "delay")
    lmin = count(min_line, "min_line")
    w = count(theiler, "theiler")
    if k < 1 or tau < 1 or lmin < 1:
        raise ValueError("m, delay and min_line must be at least 1")
    eps = real(radius, "radius")
    if not eps > 0:
        raise ValueError("radius must be positive")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    windows = x.shape[0] - (k - 1) * tau
    if windows - w < 2:
        raise ValueError("there must be at least one point outside the Theiler window")
    emb = x[np.arange(windows)[:, None] + tau * np.arange(k)[None, :]]
    points = recurrent = on_lines = longest = 0
    for s in range(w + 1, windows):
        r = np.max(np.abs(emb[s:] - emb[:-s]), axis=1) < eps
        points += r.shape[0]
        edges = np.diff(np.concatenate(([0], r.astype(np.int8), [0])))
        runs = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
        recurrent += int(np.sum(runs))
        on_lines += int(np.sum(runs[runs >= lmin]))
        if runs.shape[0] > 0:
            longest = max(longest, int(np.max(runs)))
    if recurrent == 0:
        raise ValueError("there are no recurrent points at this radius")
    return RecurrenceQuantification(recurrent / points, on_lines / recurrent, longest)


def fisher_information(samples: ArrayLike, order: int, delay: int = 1) -> float:
    """The discrete Fisher information of the normalized singular spectrum of the
    delay-embedding matrix (conventions: Fisher information; ADR 0351)."""
    m = count(order, "order")
    tau = count(delay, "delay")
    if not 2 <= m <= 32:
        raise ValueError("order must be from 2 to 32")
    if tau < 1:
        raise ValueError("delay must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    rows = x.shape[0] - (m - 1) * tau
    if rows < m:
        raise ValueError("samples are too short: need len(samples) - (order - 1)*delay >= order")
    if not np.any(x != 0):
        raise ValueError("samples must not all be 0")
    idx = np.arange(rows)[:, None] + tau * np.arange(m)[None, :]
    s = np.sort(np.linalg.svd(x[idx], compute_uv=False))[::-1]
    p = s / np.sum(s)
    head, step = p[:-1], np.diff(p)
    keep = head > 0
    return float(np.sum(step[keep] ** 2 / head[keep]))


def sample_entropy(samples: ArrayLike, m: int, r: float) -> float:
    """``-ln(A/B)``, ``B`` and ``A`` the pairs of templates that stay within ``r`` (Chebyshev)
    for ``m`` and ``m + 1`` samples (conventions: Sample entropy; ADR 0326)."""
    k = count(m, "m")
    if k < 1:
        raise ValueError("m must be at least 1")
    tol = real(r, "r")
    if tol < 0:
        raise ValueError("r must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    starts = x.shape[0] - k
    if starts < 2:
        raise ValueError("samples must be at least m + 2 long")
    t = x[np.arange(starts)[:, None] + np.arange(k + 1)[None, :]]
    b = a = 0
    for i in range(starts - 1):
        d = np.abs(t[i + 1 :] - t[i])
        near = np.max(d[:, :k], axis=1) <= tol
        b += int(np.count_nonzero(near))
        a += int(np.count_nonzero(near & (d[:, k] <= tol)))
    if b == 0:
        raise ValueError("no two templates match, so sample entropy is undefined")
    return math.inf if a == 0 else -math.log(a / b)


def permutation_entropy(samples: ArrayLike, order: int, delay: int = 1) -> float:
    """The Shannon entropy of the ordinal patterns of ``order`` samples ``delay`` apart, over
    ``ln(order!)`` (conventions: Permutation entropy; ADR 0325)."""
    m = count(order, "order")
    tau = count(delay, "delay")
    if not 2 <= m <= 8:
        raise ValueError("order must be from 2 to 8")
    if tau < 1:
        raise ValueError("delay must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    windows = x.shape[0] - (m - 1) * tau
    if windows < 1:
        raise ValueError("samples are too short for one window")
    idx = np.arange(windows)[:, None] + tau * np.arange(m)[None, :]
    patterns = np.argsort(x[idx], axis=1, kind="stable")
    _, counts = np.unique(patterns, axis=0, return_counts=True)
    p = counts / windows
    return float(-np.sum(p * np.log(p)) / math.log(math.factorial(m)))


def hjorth_parameters(samples: ArrayLike) -> HjorthParameters:
    """Activity ``var(x)``, mobility ``sqrt(var(d)/var(x))`` and complexity
    ``sqrt(var(dd)/var(d)) / mobility``, ``d`` and ``dd`` the first and second differences
    (conventions: Hjorth parameters; ADR 0324)."""
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] < 3:
        raise ValueError("samples must be a one-dimensional array of at least 3")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    d = np.diff(x)
    v0 = float(np.var(x))
    v1 = float(np.var(d))
    v2 = float(np.var(np.diff(d)))
    if not (v0 > 0 and v1 > 0):
        raise ValueError("the samples and their differences must vary")
    mobility = math.sqrt(v1 / v0)
    return HjorthParameters(v0, mobility, math.sqrt(v2 / v1) / mobility)


def temporal_centroid(samples: ArrayLike, sample_rate: float) -> TemporalCentroid:
    """The ``|x|²``-weighted mean of the sample times ``n / sample_rate``, and the weighted
    standard deviation about it (conventions: Temporal centroid; ADR 0147)."""
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] == 0:
        raise ValueError("samples must be a non-empty one-dimensional array")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    fs = float(sample_rate)
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    p = x.real * x.real + x.imag * x.imag if np.iscomplexobj(x) else x * x
    total = float(np.sum(p))
    if not total > 0:
        raise ValueError("the samples' energy must be more than 0")
    t = np.arange(x.shape[0], dtype=np.float64) / fs
    centroid = float(np.sum(p * t)) / total
    spread = math.sqrt(float(np.sum(p * (t - centroid) ** 2)) / total)
    return TemporalCentroid(centroid, spread)


def autocorrelation_pitch(
    samples: ArrayLike, sample_rate: float, min_frequency: float, max_frequency: float
) -> AutocorrelationPitch:
    """The highest biased autocorrelation peak among the lags whose ``fs/lag`` lies in
    ``[min_frequency, max_frequency]``, refined by a parabola when it is a local maximum."""
    x = np.asarray(samples)
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if x.ndim != 1 or x.shape[0] < 3:
        raise ValueError("samples must be a one-dimensional array of at least three samples")
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    fs, lo, hi = _lag_range(sample_rate, min_frequency, max_frequency)
    n = x.shape[0]
    if hi > n - 2:
        raise ValueError("min_frequency needs a lag longer than the samples allow (at most N - 2)")
    r = dsp.autocorrelation(x, hi + 1).real
    if not r[0] > 0:
        raise ValueError("the samples' energy must be more than 0")
    best, lag = _refined_peak(r, lo, hi)
    return AutocorrelationPitch(fs / lag, lag, float(r[best]) / float(r[0]))


def cepstrum_pitch(
    samples: ArrayLike,
    sample_rate: float,
    min_frequency: float,
    max_frequency: float,
    nfft: int | None = None,
) -> CepstrumPitch:
    """The highest real-cepstrum peak among the quefrencies whose ``fs/q`` lies in
    ``[min_frequency, max_frequency]``, refined by a parabola when it is a local maximum."""
    fs, lo, hi = _lag_range(sample_rate, min_frequency, max_frequency)
    c = spectral.real_cepstrum(samples, nfft)
    if 2 * hi >= c.shape[0]:
        raise ValueError("min_frequency needs a quefrency in the second half of the cepstrum")
    best, quefrency = _refined_peak(c, lo, hi)
    return CepstrumPitch(fs / quefrency, quefrency, float(c[best]))


def _lag_range(
    sample_rate: float, min_frequency: float, max_frequency: float
) -> tuple[float, int, int]:
    """The sample rate and the whole lags ``ceil(fs/max)`` to ``floor(fs/min)``, not empty."""
    fs, fmin, fmax = float(sample_rate), float(min_frequency), float(max_frequency)
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    if not (math.isfinite(fmin) and math.isfinite(fmax) and 0 < fmin <= fmax):
        raise ValueError("need 0 < min_frequency <= max_frequency, both finite")
    lo, hi = math.ceil(fs / fmax), math.floor(fs / fmin)
    if lo > hi:
        raise ValueError("no whole lag has fs/lag between min_frequency and max_frequency")
    return fs, lo, hi


def _refined_peak(values: NDArray[np.float64], lo: int, hi: int) -> tuple[int, float]:
    """The first largest value in ``lo … hi`` and its position, moved by a parabola through it
    and its neighbours when it is a strict local maximum (ADR 0150)."""
    best = lo + int(np.argmax(values[lo : hi + 1]))
    left, peak, right = float(values[best - 1]), float(values[best]), float(values[best + 1])
    curve = left - 2 * peak + right
    delta = (left - right) / (2 * curve) if peak >= left and peak >= right and curve < 0 else 0.0
    return best, best + delta


def power_ccdf(samples: ArrayLike, levels_db: ArrayLike) -> PowerCcdf:
    """For each level ``L`` in dB, the fraction of samples with ``|x|^2 > mean * 10**(L/10)``
    (strict; conventions: Power CCDF; ADR 0119)."""
    p, mean = _instantaneous_power(samples)
    levels = np.asarray(levels_db, dtype=np.float64)
    if levels.ndim != 1 or levels.size == 0 or not np.all(np.isfinite(levels)):
        raise ValueError("levels_db must be a non-empty list of finite values")
    probs = np.array(
        [np.count_nonzero(p > mean * 10.0 ** (float(v) / 10)) / p.size for v in levels]
    )
    return PowerCcdf(mean, levels.copy(), probs)


def power_ccdf_level(samples: ArrayLike, probability: float) -> float:
    """The smallest level in dB above the mean power whose CCDF is at most ``probability``: the
    ``(floor(probability*N) + 1)``-th largest power over the mean (conventions: Power CCDF)."""
    q = real(probability, "probability")
    if not 0 < q < 1:
        raise ValueError("probability must be in (0, 1)")
    p, mean = _instantaneous_power(samples)
    m = math.floor(q * p.size)
    t = float(np.sort(p)[p.size - 1 - m])
    return 10 * (math.log10(t) - math.log10(mean)) if t > 0 else -math.inf


def kay_frequency(samples: ArrayLike, sample_rate: float) -> float:
    """A complex tone's frequency in Hz by Kay's weighted phase-difference estimator
    (conventions: Single-tone frequency (Kay); ADR 0123)."""
    fs = real(sample_rate, "sample_rate")
    if not fs > 0:
        raise ValueError("sample_rate must be positive")
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] < 2:
        raise ValueError("samples must be a one-dimensional array of at least two samples")
    x = x.astype(np.complex128)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if np.any(x == 0):
        raise ValueError("samples must be non-zero")
    a, b = x.real[1:], x.imag[1:]
    c, d = x.real[:-1], x.imag[:-1]
    steps = np.arctan2(b * c - a * d, a * c + b * d)
    n_total = x.size
    n = np.arange(n_total - 1, dtype=np.float64)
    half = n_total / 2
    w = 3 * n_total / (2 * (n_total * n_total - 1)) * (1 - ((n - (half - 1)) / half) ** 2)
    return fs * float(np.sum(w * steps)) / (2 * math.pi)


@dataclass(frozen=True)
class ToneMetrics:
    """SNR, SINAD, THD and ENOB of one tone (conventions: Tone metrics).

    Powers are in sample units squared, summed over bin groups of one windowed spectrum.
    ``fundamental_frequency`` is the power-weighted centroid of the fundamental's group, in Hz.
    """

    fundamental_frequency: float
    signal_power: float
    harmonic_power: float
    noise_power: float
    dc_power: float
    snr_db: float
    sinad_db: float
    thd_db: float
    enob: float


def tone_metrics(
    samples: ArrayLike,
    sample_rate: float,
    *,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
    num_harmonics: int = 5,
    fundamental: float | None = None,
) -> ToneMetrics:
    """SNR, SINAD, THD and ENOB of the strongest tone (or the one at ``fundamental``).

    ``width`` is the half-width of each bin group, by default set by the window; harmonics
    ``2 … num_harmonics + 1`` are found at multiples of the fundamental, aliased.
    """
    harmonics = count(num_harmonics, "num_harmonics")
    g = _Groups(samples, sample_rate, window, beta, width, fundamental)
    fs = g.d.sample_rate
    harmonic = 0.0
    for h in range(2, harmonics + 2):
        if g.d.one_sided:
            x = (h * g.f1) % fs
            x = fs - x if x > fs / 2 else x
        else:
            x = (h * g.f1 + fs / 2) % fs - fs / 2
        harmonic += g.power(g.group(g.nearest(x)))
    noise = float(np.sum(g.p[~g.claimed]))
    sinad = _db(g.signal, noise + harmonic)
    return ToneMetrics(
        fundamental_frequency=g.f1,
        signal_power=g.signal,
        harmonic_power=harmonic,
        noise_power=noise,
        dc_power=g.power(g.dc),
        snr_db=_db(g.signal, noise),
        sinad_db=sinad,
        thd_db=-_db(g.signal, harmonic),
        enob=(sinad - 10 * math.log10(1.5)) / (20 * math.log10(2)),
    )


@dataclass(frozen=True, eq=False)
class Sfdr:
    """Spurious-free dynamic range and the strongest spurs (conventions: Spurs and SFDR).

    The carrier is the tone metrics' fundamental group. Spurs are the next strongest groups, DC
    excluded, strongest peak bin first: ``spur_powers`` in sample units squared,
    ``spur_frequencies`` their power centroids in Hz, ``spur_dbc`` each relative to the carrier.
    ``sfdr_db`` is minus the first spur's dBc, +inf when there is no spur.
    """

    carrier_frequency: float
    carrier_power: float
    sfdr_db: float
    spur_frequencies: NDArray[np.float64]
    spur_powers: NDArray[np.float64]
    spur_dbc: NDArray[np.float64]


def sfdr(
    samples: ArrayLike,
    sample_rate: float,
    *,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
    fundamental: float | None = None,
    num_spurs: int = 1,
) -> Sfdr:
    """SFDR of the strongest tone (or the one at ``fundamental``) and up to ``num_spurs`` spurs.

    Groups are formed as for :func:`tone_metrics`; after DC and the carrier, each spur is the group
    around the strongest bin left, until ``num_spurs`` are found or no bin with power is left.
    """
    wanted = count(num_spurs, "num_spurs")
    if wanted < 1:
        raise ValueError("num_spurs must be at least 1")
    g = _Groups(samples, sample_rate, window, beta, width, fundamental)
    freqs: list[float] = []
    powers: list[float] = []
    while len(powers) < wanted:
        free = np.flatnonzero(~g.claimed)
        if free.size == 0:
            break
        c = int(free[np.argmax(g.p[free])])
        if not g.p[c] > 0:
            break
        idx = g.group(c)
        power = g.power(idx)
        freqs.append(g.centroid(idx, power))
        powers.append(power)
    dbc = np.array([10 * math.log10(v / g.signal) for v in powers], dtype=np.float64)
    return Sfdr(
        carrier_frequency=g.f1,
        carrier_power=g.signal,
        sfdr_db=-float(dbc[0]) if powers else math.inf,
        spur_frequencies=np.array(freqs, dtype=np.float64),
        spur_powers=np.array(powers, dtype=np.float64),
        spur_dbc=dbc,
    )


@dataclass(frozen=True, eq=False)
class TwoToneImd:
    """Third-order intermodulation of two tones (conventions: Two-tone intermodulation).

    Tones and products come lower first. ``imd_dbc`` is each product relative to the mean tone
    power; ``ip3_db`` is the third-order intercept from the worse product, in dB of sample
    units squared.
    """

    tone_frequencies: NDArray[np.float64]
    tone_powers: NDArray[np.float64]
    imd_frequencies: NDArray[np.float64]
    imd_powers: NDArray[np.float64]
    imd_dbc: NDArray[np.float64]
    worst_imd_dbc: float
    ip3_db: float


def two_tone_imd(
    samples: ArrayLike,
    sample_rate: float,
    f1: float,
    f2: float,
    *,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
) -> TwoToneImd:
    """The tones at ``f1 < f2`` and their third-order products ``2*f1 - f2`` and ``2*f2 - f1``,
    grouped as for :func:`tone_metrics` (conventions: Two-tone intermodulation; ADR 0107)."""
    t = _two_tones(
        samples, sample_rate, f1, f2, window, beta, width, lambda a, b: (2 * a - b, 2 * b - a)
    )
    return TwoToneImd(*t[:6], ip3_db=t[6] - t[5] / 2)


@dataclass(frozen=True, eq=False)
class TwoToneIp2:
    """Second-order intermodulation of two tones (conventions: Two-tone intermodulation).

    The products come difference ``f2 - f1`` first, then sum ``f1 + f2``. ``imd_dbc`` is each
    relative to the mean tone power; ``ip2_db`` is the second-order intercept from the worse
    product, in dB of sample units squared.
    """

    tone_frequencies: NDArray[np.float64]
    tone_powers: NDArray[np.float64]
    imd_frequencies: NDArray[np.float64]
    imd_powers: NDArray[np.float64]
    imd_dbc: NDArray[np.float64]
    worst_imd_dbc: float
    ip2_db: float


def two_tone_ip2(
    samples: ArrayLike,
    sample_rate: float,
    f1: float,
    f2: float,
    *,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
) -> TwoToneIp2:
    """The tones at ``f1 < f2`` and their second-order products ``f2 - f1`` and ``f1 + f2``,
    grouped as for :func:`two_tone_imd` (conventions: Two-tone intermodulation; ADR 0110)."""
    t = _two_tones(samples, sample_rate, f1, f2, window, beta, width, lambda a, b: (b - a, a + b))
    return TwoToneIp2(*t[:6], ip2_db=t[6] - t[5])


@dataclass(frozen=True, eq=False)
class TwoToneIp5:
    """Fifth-order intermodulation of two tones (conventions: Two-tone intermodulation).

    The products come lower ``3*f1 - 2*f2`` first, then upper ``3*f2 - 2*f1``. ``imd_dbc`` is
    each relative to the mean tone power; ``ip5_db`` is the fifth-order intercept from the worse
    product, in dB of sample units squared.
    """

    tone_frequencies: NDArray[np.float64]
    tone_powers: NDArray[np.float64]
    imd_frequencies: NDArray[np.float64]
    imd_powers: NDArray[np.float64]
    imd_dbc: NDArray[np.float64]
    worst_imd_dbc: float
    ip5_db: float


def two_tone_ip5(
    samples: ArrayLike,
    sample_rate: float,
    f1: float,
    f2: float,
    *,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
) -> TwoToneIp5:
    """The tones at ``f1 < f2`` and their fifth-order products ``3*f1 - 2*f2`` and
    ``3*f2 - 2*f1``, grouped as for :func:`two_tone_imd` (conventions: Two-tone intermodulation;
    ADR 0117)."""
    t = _two_tones(
        samples,
        sample_rate,
        f1,
        f2,
        window,
        beta,
        width,
        lambda a, b: (3 * a - 2 * b, 3 * b - 2 * a),
    )
    return TwoToneIp5(*t[:6], ip5_db=t[6] - t[5] / 4)


def _two_tones(
    samples: ArrayLike,
    sample_rate: float,
    f1: float,
    f2: float,
    window: str,
    beta: float | None,
    width: int | None,
    products: Callable[[float, float], tuple[float, float]],
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    float,
    float,
]:
    """Tone frequencies and powers, product frequencies, powers and dBc, the worst dBc and the
    mean tone power in dB, for the two products at ``products(f1, f2)``."""
    lo = real(f1, "f1")
    hi = real(f2, "f2")
    if not lo < hi:
        raise ValueError("f1 must be below f2")
    g = _Groups(samples, sample_rate, window, beta, width, lo)
    fs = g.d.sample_rate
    if not (abs(hi) <= fs / 2 and (hi >= 0 or not g.d.one_sided)):
        raise ValueError("f2 must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)")
    c = g.nearest(g.alias(hi))
    if g.claimed[c]:
        raise ValueError("f2 falls in the DC group or the f1 group")
    idx = g.group(c)
    p2 = g.power(idx)
    if not p2 > 0:
        raise ValueError("no signal power at f2")
    imd_f = [g.alias(x) for x in products(lo, hi)]
    imd_p = []
    for x in imd_f:
        k = g.nearest(x)
        if g.claimed[k]:
            raise ValueError("an intermodulation product falls on DC, a tone or the other product")
        imd_p.append(g.power(g.group(k)))
    pt = (g.signal + p2) / 2
    dbc = [10 * math.log10(p / pt) if p > 0 else -math.inf for p in imd_p]
    return (
        np.array([g.f1, g.centroid(idx, p2)], dtype=np.float64),
        np.array([g.signal, p2], dtype=np.float64),
        np.array(imd_f, dtype=np.float64),
        np.array(imd_p, dtype=np.float64),
        np.array(dbc, dtype=np.float64),
        max(dbc),
        10 * math.log10(pt),
    )


@dataclass(frozen=True, eq=False)
class PhaseNoise:
    """Single-sideband phase noise of a carrier (conventions: Phase noise measurement).

    ``l_dbc_hz`` is ``L`` at each of ``offsets``: the mean PSD of the two sidebands relative to
    ``carrier_power``, in dBc/Hz.
    """

    carrier_frequency: float
    carrier_power: float
    offsets: NDArray[np.float64]
    l_dbc_hz: NDArray[np.float64]


@dataclass(frozen=True, eq=False)
class IntegratedPhaseNoise:
    """Phase noise integrated over an offset band (conventions: Integrated phase noise).

    ``integrated_dbc`` is the band's power on both sides of the carrier relative to
    ``carrier_power``; ``phase_rms`` its square root in radians, ``jitter_rms`` that over
    ``2*pi*|carrier_frequency|`` in seconds.
    """

    carrier_frequency: float
    carrier_power: float
    f_lo: float
    f_hi: float
    integrated_dbc: float
    phase_rms: float
    jitter_rms: float


@dataclass(frozen=True, eq=False)
class PhaseNoiseSpurs:
    """Discrete spurs standing above the phase noise (conventions: Phase noise spur finder).

    ``offsets`` are each spur's bin frequency minus ``carrier_frequency``, signed, in Hz;
    ``levels_dbc`` the group's power above the line between its edges, relative to
    ``carrier_power``. Pass ``abs(offsets)`` as ``spur_offsets`` to remove them.
    """

    carrier_frequency: float
    carrier_power: float
    offsets: NDArray[np.float64]
    levels_dbc: NDArray[np.float64]


@dataclass(frozen=True)
class _Carrier:
    d: spectral.SpectralDensity
    c: int  # the carrier bin
    w: int  # the group's half-width
    pc: float
    fc: float

    def check_reach(self, o: float, what: str) -> None:
        fs = self.d.sample_rate
        lo = 0.0 if self.d.one_sided else -fs / 2
        if not (
            self.fc - o >= lo
            and (self.fc + o <= fs / 2 if self.d.one_sided else self.fc + o < fs / 2)
        ):
            raise ValueError(f"{what} reaches past the spectrum")

    def nearest(self, freq: float) -> int:
        k = math.floor((freq - float(self.d.frequencies[0])) / self.d.bin_width + 0.5)
        return min(max(k, 0), self.d.psd.size - 1)


def _carrier(
    samples: ArrayLike,
    sample_rate: float,
    carrier: float | None,
    nperseg: int | None,
    window: str,
    beta: float | None,
    width: int | None,
) -> _Carrier:
    """The Welch PSD, its carrier bin and group (conventions: Phase noise measurement)."""
    if np.asarray(samples).size < 2:
        raise ValueError("phase noise needs at least two samples")
    seg = None if nperseg is None else count(nperseg, "nperseg")
    w_given = None if width is None else count(width, "width")
    given = None if carrier is None else real(carrier, "carrier")
    with np.errstate(over="ignore"):  # an overflowing spectrum is rejected below
        d = spectral.welch_psd(samples, sample_rate, nperseg=seg, window=window, beta=beta)
    fs = d.sample_rate
    p = d.psd * d.bin_width
    if not math.isfinite(float(np.sum(p))):
        raise ValueError("samples must be finite and small enough for a finite spectrum")
    w = _half_width(window, beta) if w_given is None else w_given
    if given is None:
        c = int(np.argmax(d.psd))
    else:
        if not (abs(given) <= fs / 2 and (given >= 0 or not d.one_sided)):
            raise ValueError(
                "carrier must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)"
            )
        if not d.one_sided:
            given = (given + fs / 2) % fs - fs / 2  # +fs/2 is the bin at -fs/2
        c = _Carrier(d, 0, 0, 0.0, 0.0).nearest(given)
    group = slice(max(c - w, 0), min(c + w, d.psd.size - 1) + 1)
    pc = float(np.sum(p[group]))
    if not pc > 0:
        raise ValueError("no power at the carrier")
    fc = float(np.sum(p[group] * d.frequencies[group])) / pc
    return _Carrier(d, c, w, pc, fc)


def _spur_list(spur_offsets: ArrayLike | None) -> list[float]:
    if spur_offsets is None:
        return []
    s = np.asarray(spur_offsets, dtype=np.float64)
    if s.ndim != 1:
        raise ValueError("spur_offsets must be one-dimensional")
    if not np.all(np.isfinite(s) & (s > 0)):
        raise ValueError("spur_offsets must be finite and positive")
    return [float(v) for v in s]


def _without_spurs(k: _Carrier, spurs: list[float]) -> NDArray[np.float64]:
    """A copy of the PSD with each spur's group, on each side, replaced by a straight line between
    the bins just outside it (conventions: Phase noise with spurs removed; ADR 0115)."""
    psd = np.array(k.d.psd, dtype=np.float64)
    fs = k.d.sample_rate
    lo = 0.0 if k.d.one_sided else -fs / 2
    n = psd.size
    for o in spurs:
        for f in (k.fc - o, k.fc + o):
            if not (f >= lo and (f <= fs / 2 if k.d.one_sided else f < fs / 2)):
                continue
            s = k.nearest(f)
            if abs(s - k.c) <= 2 * k.w + 1:
                raise ValueError("a spur's group reaches the carrier group")
            a, b = s - k.w - 1, s + k.w + 1
            va = float(psd[a]) if a >= 0 else float(psd[b])
            vb = float(psd[b]) if b < n else va
            for j in range(max(a + 1, 0), min(b - 1, n - 1) + 1):
                psd[j] = va + (vb - va) * (j - a) / (2 * k.w + 2)
    return psd


def phase_noise_ssb(
    samples: ArrayLike,
    sample_rate: float,
    offsets: ArrayLike,
    *,
    carrier: float | None = None,
    nperseg: int | None = None,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
    spur_offsets: ArrayLike | None = None,
) -> PhaseNoise:
    """``L(f)`` in dBc/Hz at each offset from the strongest bin (or the one at ``carrier``), from
    a Welch PSD, with any ``spur_offsets`` removed first (conventions: Phase noise measurement;
    ADR 0108, 0115)."""
    off = np.asarray(offsets, dtype=np.float64)
    if off.ndim != 1 or off.size == 0:
        raise ValueError("offsets must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(off) & (off > 0)):
        raise ValueError("offsets must be finite and positive")
    spurs = _spur_list(spur_offsets)
    k = _carrier(samples, sample_rate, carrier, nperseg, window, beta, width)
    psd = _without_spurs(k, spurs)
    out = np.empty(off.size)
    for i, o in enumerate(off.tolist()):
        k.check_reach(o, "an offset")
        ka, kb = k.nearest(k.fc - o), k.nearest(k.fc + o)
        if abs(ka - k.c) <= k.w or abs(kb - k.c) <= k.w:
            raise ValueError("an offset falls in the carrier group")
        s = (float(psd[ka]) + float(psd[kb])) / 2
        out[i] = 10 * math.log10(s / k.pc) if s > 0 else -math.inf
    return PhaseNoise(k.fc, k.pc, off.copy(), out)


def integrated_phase_noise(
    samples: ArrayLike,
    sample_rate: float,
    f_lo: float,
    f_hi: float,
    *,
    carrier: float | None = None,
    nperseg: int | None = None,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
    spur_offsets: ArrayLike | None = None,
) -> IntegratedPhaseNoise:
    """RMS phase error and jitter from the PSD over offsets ``f_lo ... f_hi`` on both sides of the
    carrier, whole bins only, with any ``spur_offsets`` removed first (conventions: Integrated
    phase noise; ADR 0109, 0115)."""
    lo, hi = real(f_lo, "f_lo"), real(f_hi, "f_hi")
    if not 0 < lo < hi < math.inf:
        raise ValueError("the band needs 0 < f_lo < f_hi, finite")
    spurs = _spur_list(spur_offsets)
    k = _carrier(samples, sample_rate, carrier, nperseg, window, beta, width)
    k.check_reach(hi, "the band")
    off = np.abs(k.d.frequencies - k.fc)
    band = (off >= lo) & (off <= hi)
    bins = np.flatnonzero(band)
    if np.any(np.abs(bins - k.c) <= k.w):
        raise ValueError("the band reaches into the carrier group")
    ratio = float(np.sum(_without_spurs(k, spurs)[band])) * k.d.bin_width / k.pc
    rms = math.sqrt(ratio)
    if k.fc != 0:
        jitter = rms / (2 * math.pi * abs(k.fc))
    else:
        jitter = math.inf if rms > 0 else 0.0
    dbc = 10 * math.log10(ratio) if ratio > 0 else -math.inf
    return IntegratedPhaseNoise(k.fc, k.pc, lo, hi, dbc, rms, jitter)


def phase_noise_spurs(
    samples: ArrayLike,
    sample_rate: float,
    f_lo: float,
    f_hi: float,
    *,
    threshold_db: float = 10.0,
    carrier: float | None = None,
    nperseg: int | None = None,
    window: str = "blackman_harris",
    beta: float | None = None,
    width: int | None = None,
) -> PhaseNoiseSpurs:
    """The bins in the offset band ``f_lo ... f_hi`` whose group stands ``threshold_db`` above the
    straight line between its edge bins, each the peak of its group (conventions: Phase noise spur
    finder; ADR 0116)."""
    lo, hi = real(f_lo, "f_lo"), real(f_hi, "f_hi")
    if not 0 < lo < hi < math.inf:
        raise ValueError("the band needs 0 < f_lo < f_hi, finite")
    t = real(threshold_db, "threshold_db")
    if not 0 < t < math.inf:
        raise ValueError("threshold_db must be finite and positive")
    k = _carrier(samples, sample_rate, carrier, nperseg, window, beta, width)
    k.check_reach(hi, "the band")
    p = k.d.psd * k.d.bin_width
    p = np.where(p <= _FLOOR * float(np.sum(p)), 0.0, p)
    off = np.abs(k.d.frequencies - k.fc)
    bins = np.flatnonzero((off >= lo) & (off <= hi))
    w, n = k.w, p.size
    if np.any(np.abs(bins - k.c) <= 2 * w + 1):
        raise ValueError("the band reaches within 2w + 1 bins of the carrier")
    ratio = 10 ** (t / 10)
    offsets: list[float] = []
    levels: list[float] = []
    for j in bins.tolist():
        a, b = j - w - 1, j + w + 1
        if a < 0 or b >= n:
            continue
        pj = float(p[j])
        if not all(pj > float(p[i]) for i in range(j - w, j)):
            continue
        if not all(pj >= float(p[i]) for i in range(j + 1, j + w + 1)):
            continue
        g = 0.0
        for i in range(a + 1, b):
            g += float(p[i])
        line = (2 * w + 1) * (float(p[a]) + float(p[b])) / 2
        if g > line * ratio:
            offsets.append(float(k.d.frequencies[j]) - k.fc)
            levels.append(10 * math.log10((g - line) / k.pc))
    return PhaseNoiseSpurs(
        k.fc, k.pc, np.array(offsets, dtype=np.float64), np.array(levels, dtype=np.float64)
    )


_FLOOR = 1e-20  # bins at or below this fraction of the total power are rounding error: zero


class _Groups:
    """One windowed spectrum's bins, claimed group by group: DC, then the fundamental
    (conventions: Tone metrics). Later groups are claimed by the caller."""

    def __init__(
        self,
        samples: ArrayLike,
        sample_rate: float,
        window: str,
        beta: float | None,
        width: int | None,
        fundamental: float | None,
    ) -> None:
        if np.asarray(samples).size < 2:
            raise ValueError("tone metrics need at least two samples")
        w_given = None if width is None else count(width, "width")
        given = None if fundamental is None else real(fundamental, "fundamental")
        with np.errstate(over="ignore"):  # an overflowing spectrum is rejected below
            d = spectral.welch_psd(samples, sample_rate, window=window, beta=beta)
        fs = d.sample_rate
        if given is not None and not (abs(given) <= fs / 2 and (given >= 0 or not d.one_sided)):
            raise ValueError(
                "fundamental must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)"
            )
        if given is not None and not d.one_sided:
            given = (given + fs / 2) % fs - fs / 2  # +fs/2 is the bin at -fs/2
        self.d = d
        self.w = _half_width(window, beta) if w_given is None else w_given
        p = d.psd * d.bin_width
        total = float(np.sum(p))
        if not math.isfinite(total):
            raise ValueError("samples must be finite and small enough for a finite spectrum")
        self.p: NDArray[np.float64] = np.where(p <= _FLOOR * total, 0.0, p)
        self.f = d.frequencies
        self.claimed = np.zeros(self.p.size, dtype=bool)
        self.dc = self.group(self.nearest(0.0))
        if given is None:
            free = np.flatnonzero(~self.claimed)
            if free.size == 0:
                raise ValueError("no bins are left for the fundamental after the DC group")
            c = int(free[np.argmax(self.p[free])])
        else:
            c = self.nearest(given)
            if self.claimed[c]:
                raise ValueError("the fundamental falls in the DC group")
        fund = self.group(c)
        self.signal = self.power(fund)
        if not self.signal > 0:
            raise ValueError("no signal power at the fundamental")
        self.f1 = self.centroid(fund, self.signal)

    def alias(self, freq: float) -> float:
        """``freq`` in the spectrum's range: folded for real input, wrapped for complex."""
        fs = self.d.sample_rate
        if self.d.one_sided:
            x = freq % fs
            return fs - x if x > fs / 2 else x
        return (freq + fs / 2) % fs - fs / 2

    def nearest(self, freq: float) -> int:
        """Index of the bin nearest ``freq``, clipped to the spectrum."""
        k = math.floor((freq - float(self.f[0])) / self.d.bin_width + 0.5)
        return min(max(k, 0), self.p.size - 1)

    def group(self, c: int) -> NDArray[np.intp]:
        """Claims and returns the unclaimed bins within the half-width of bin ``c``."""
        idx = np.arange(max(c - self.w, 0), min(c + self.w, self.p.size - 1) + 1)
        free: NDArray[np.intp] = idx[~self.claimed[idx]]
        self.claimed[free] = True
        return free

    def power(self, idx: NDArray[np.intp]) -> float:
        return float(np.sum(self.p[idx]))

    def centroid(self, idx: NDArray[np.intp], power: float) -> float:
        return float(np.sum(self.p[idx] * self.f[idx])) / power


@dataclass(frozen=True)
class NoiseFigure:
    """A Y-factor noise figure measurement (conventions: Noise figure).

    ``y_factor`` is hot over cold power, ``noise_factor`` the linear F, ``noise_figure_db``
    ``10*log10(F)`` and ``noise_temperature`` ``290*(F - 1)`` in kelvin.
    """

    y_factor: float
    noise_factor: float
    noise_figure_db: float
    noise_temperature: float


_T0 = 290.0


def noise_figure_y_factor(
    hot_power: float, cold_power: float, enr_db: float, *, cold_temperature: float = 290.0
) -> NoiseFigure:
    """Noise figure from the output powers with a noise source hot and cold (conventions: Noise
    figure; ADR 0105): ``F = (ENR - Y*(T_c/T0 - 1))/(Y - 1)``, ``T0 = 290 K``."""
    hot = real(hot_power, "hot_power")
    cold = real(cold_power, "cold_power")
    if not cold > 0:
        raise ValueError("cold_power must be positive")
    if not hot > cold:
        raise ValueError("hot_power must be greater than cold_power")
    e = real(enr_db, "enr_db")
    tc = real(cold_temperature, "cold_temperature")
    if not tc > 0:
        raise ValueError("cold_temperature must be positive")
    try:
        enr = 10.0 ** (e / 10)
    except OverflowError:
        raise ValueError("enr_db is too large") from None
    y = hot / cold
    f = (enr - y * (tc / _T0 - 1)) / (y - 1)
    if not (math.isfinite(f) and f > 0):
        raise ValueError("the measurement gives no finite positive noise factor")
    return NoiseFigure(y, f, 10 * math.log10(f), _T0 * (f - 1))


@dataclass(frozen=True)
class CascadeNoiseFigure:
    """The noise figure of stages in a chain (conventions: Noise figure, Cascade).

    ``contributions`` holds each stage's term of Friis' sum, in chain order; ``gain_db`` is the
    total gain.
    """

    noise_factor: float
    noise_figure_db: float
    noise_temperature: float
    gain_db: float
    contributions: NDArray[np.float64]


def noise_figure_cascade(noise_figures_db: ArrayLike, gains_db: ArrayLike) -> CascadeNoiseFigure:
    """Friis' noise factor of matched stages in chain order (conventions: Noise figure, Cascade;
    ADR 0106): ``F = F1 + (F2 - 1)/G1 + (F3 - 1)/(G1*G2) + ...``."""
    nf = np.asarray(noise_figures_db, dtype=np.float64)
    g = np.asarray(gains_db, dtype=np.float64)
    if nf.ndim != 1 or g.ndim != 1:
        raise ValueError("noise_figures_db and gains_db must be one-dimensional")
    if nf.size == 0 or nf.size != g.size:
        raise ValueError("noise_figures_db and gains_db need the same number of stages, at least 1")
    if not (np.all(np.isfinite(nf)) and np.all(np.isfinite(g))):
        raise ValueError("noise figures and gains must be finite")
    if np.any(nf < 0):
        raise ValueError("noise figures must not be negative")
    c = np.empty(nf.size)
    before = 1.0
    total = 0.0
    gain_db = 0.0
    for i in range(nf.size):
        f = _from_db(float(nf[i]))
        # a gain that underflowed to 0 leaves no finite factor, as the C# division does
        c[i] = f if i == 0 else ((f - 1) / before if before else math.inf)
        total += float(c[i])
        before *= _from_db(float(g[i]))
        gain_db += float(g[i])
    if not math.isfinite(total):
        raise ValueError("the gains before a noisy stage underflow: no finite noise factor")
    return CascadeNoiseFigure(total, 10 * math.log10(total), _T0 * (total - 1), gain_db, c)


@dataclass(frozen=True, eq=False)
class GainCompression:
    """Gain compression from a drive sweep (conventions: Gain compression; ADR 0112).

    ``gain_db`` and ``compression`` hold one value per step; the points are NaN when no step
    compresses by ``compression_db``.
    """

    small_signal_gain_db: float
    gain_db: NDArray[np.float64]
    compression: NDArray[np.float64]
    input_point_db: float
    output_point_db: float
    saturated_output_db: float


def gain_compression(
    input_db: ArrayLike,
    output_db: ArrayLike,
    *,
    compression_db: float = 1.0,
    linear_points: int = 1,
) -> GainCompression:
    """Small-signal gain (the mean over the first ``linear_points`` steps) and the point where
    the gain has fallen by ``compression_db``, interpolated linearly in dB between sweep steps
    (conventions: Gain compression; ADR 0112)."""
    x = np.asarray(input_db, dtype=np.float64)
    y = np.asarray(output_db, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("input_db and output_db must be one-dimensional")
    if x.size < 2 or x.size != y.size:
        raise ValueError("input_db and output_db need the same number of steps, at least 2")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        raise ValueError("input and output levels must be finite")
    if not np.all(np.diff(x) > 0):
        raise ValueError("input_db must be strictly ascending")
    c_db = real(compression_db, "compression_db")
    if not c_db > 0:
        raise ValueError("compression_db must be positive")
    lin = count(linear_points, "linear_points")
    if not 1 <= lin <= x.size:
        raise ValueError("linear_points must be from 1 to the number of steps")
    g = y - x
    total = 0.0
    for v in g[:lin]:
        total += float(v)
    gss = total / lin
    c = gss - g
    point = math.nan
    for k in range(x.size):
        if c[k] >= c_db:
            if k == 0:
                point = float(x[0])
            else:
                t = (c_db - float(c[k - 1])) / (float(c[k]) - float(c[k - 1]))
                point = float(x[k - 1]) + t * (float(x[k]) - float(x[k - 1]))
            break
    return GainCompression(gss, g, c, point, point + gss - c_db, float(np.max(y)))


@dataclass(frozen=True, eq=False)
class AmAmPm:
    """AM/AM and AM/PM by input-level bin (conventions: AM/AM and AM/PM; ADR 0113).

    An empty bin has ``counts`` 0 and NaN gain and phase.
    """

    levels_db: NDArray[np.float64]
    counts: NDArray[np.int64]
    gain_db: NDArray[np.float64]
    phase_deg: NDArray[np.float64]


def am_am_pm(input: ArrayLike, output: ArrayLike, edges_db: ArrayLike) -> AmAmPm:
    """Gain in dB and phase in degrees of the mean complex ratio ``y/x`` in each bin of input
    level ``20 log10|x|`` (conventions: AM/AM and AM/PM; ADR 0113)."""
    x = np.asarray(input, dtype=np.complex128)
    y = np.asarray(output, dtype=np.complex128)
    e = np.asarray(edges_db, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or e.ndim != 1:
        raise ValueError("input, output and edges_db must be one-dimensional")
    if x.size == 0 or x.size != y.size:
        raise ValueError("input and output need the same number of samples, at least 1")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        raise ValueError("input and output must be finite")
    if e.size < 2 or not np.all(np.isfinite(e)) or not np.all(np.diff(e) > 0):
        raise ValueError("edges_db must be at least 2 finite, strictly ascending values")
    nb = e.size - 1
    sums = [0j] * nb
    counts = np.zeros(nb, dtype=np.int64)
    with np.errstate(divide="ignore"):
        levels = 20 * np.log10(np.abs(x))
    for k in range(x.size):
        lv = float(levels[k])
        if not e[0] <= lv <= e[-1]:
            continue  # outside every bin, or x = 0
        i = min(int(np.searchsorted(e, lv, side="right")) - 1, nb - 1)
        sums[i] += complex(y[k]) / complex(x[k])
        counts[i] += 1
    gain = np.full(nb, math.nan)
    phase = np.full(nb, math.nan)
    for i in range(nb):
        if counts[i]:
            h = sums[i] / int(counts[i])
            gain[i] = 20 * math.log10(abs(h)) if h != 0 else -math.inf
            phase[i] = math.atan2(h.imag, h.real) * 180 / math.pi if h != 0 else 0.0
    return AmAmPm((e[:-1] + e[1:]) / 2, counts, gain, phase)


def _from_db(db: float) -> float:
    """10**(db/10), +inf where it overflows (as in C#)."""
    try:
        return float(10.0 ** (db / 10))
    except OverflowError:
        return math.inf


def _half_width(window: str, beta: float | None) -> int:
    if window == "kaiser":
        if beta is None:
            raise ValueError("the kaiser window needs beta")
        return math.ceil(math.sqrt(1 + (beta / math.pi) ** 2))
    return len(spectral._COSINE_SUMS[window])


def _db(num: float, den: float) -> float:
    """10*log10(num/den) for num > 0; +inf when den is zero."""
    return math.inf if den == 0 else 10 * math.log10(num / den)


def time_weighting(
    samples: ArrayLike, sample_rate: float, time_constant: float
) -> NDArray[np.float64]:
    """The exponential time weighting ``y[n] = a y[n-1] + (1 - a)|x[n]|^2``, ``a =
    exp(-1/(time_constant sample_rate))``, from 0 (conventions: Time weighting; ADR 0166)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be a one-dimensional array")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    fs = float(sample_rate)
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    tau = float(time_constant)
    if not (math.isfinite(tau) and tau > 0):
        raise ValueError("time_constant must be finite and positive")
    p = x.real * x.real + x.imag * x.imag if np.iscomplexobj(x) else x * x
    gain = -math.expm1(-1.0 / (tau * fs))
    alpha = 1.0 - gain
    out = np.empty(p.shape[0], dtype=np.float64)
    y = 0.0
    for n, v in enumerate(p.tolist()):
        y = alpha * y + gain * v
        out[n] = y
    return out


def octave_band_levels(
    samples: ArrayLike,
    sample_rate: float,
    fraction: int,
    min_frequency: float,
    max_frequency: float,
    *,
    order: int = 3,
) -> NDArray[np.float64]:
    """The mean power in each band of ``octave_bands(fraction, min_frequency, max_frequency)``,
    through a Butterworth band-pass from rest (conventions: Octave-band levels; ADR 0168)."""
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] == 0:
        raise ValueError("samples must be a non-empty one-dimensional array")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    n = count(order, "order")
    if n < 1:
        raise ValueError("order must be at least 1")
    bands = units.octave_bands(fraction, min_frequency, max_frequency)
    if bands.shape[0] and bands[-1, 2] >= fs / 2:
        raise ValueError("every band's upper edge must be below sample_rate / 2")
    out = np.empty(bands.shape[0], dtype=np.float64)
    for i, (lower, _, upper) in enumerate(bands.tolist()):
        y = dsp.IirFilter(dsp.butterworth_bandpass(n, lower, upper, fs)).process(x)
        out[i] = float(np.mean(y.real * y.real + y.imag * y.imag))
    return out


def exceedance_levels(powers: ArrayLike, percents: ArrayLike) -> NDArray[np.float64]:
    """The level exceeded ``N`` % of the time for each ``N`` in ``percents``: the ``1 - N/100``
    quantile of ``powers`` by linear interpolation (conventions: Exceedance levels; ADR 0169)."""
    p = np.asarray(powers, dtype=np.float64)
    if p.ndim != 1 or p.shape[0] == 0:
        raise ValueError("powers must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(p)) or np.any(p < 0):
        raise ValueError("powers must be finite and non-negative")
    pct = np.asarray(percents, dtype=np.float64)
    if pct.ndim != 1:
        raise ValueError("percents must be a one-dimensional array")
    if not np.all(np.isfinite(pct)) or np.any((pct < 0) | (pct > 100)):
        raise ValueError("percents must be finite and in [0, 100]")
    s = np.sort(p).tolist()
    out = np.empty(pct.shape[0], dtype=np.float64)
    for i, n in enumerate(pct.tolist()):
        h = (len(s) - 1) * (1 - n / 100)
        k = min(math.floor(h), len(s) - 1)
        out[i] = s[k] if k == len(s) - 1 else s[k] + (h - k) * (s[k + 1] - s[k])
    return out


def _level_powers(samples: ArrayLike, sample_rate: float) -> tuple[NDArray[np.float64], float]:
    """``|x|^2`` of finite one-dimensional real or complex samples, and the checked rate."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be a one-dimensional array")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    return np.asarray(x.real * x.real + x.imag * x.imag, dtype=np.float64), fs


def block_leq(samples: ArrayLike, sample_rate: float, duration: float) -> NDArray[np.float64]:
    """The mean ``|x|^2`` over consecutive blocks of ``round(duration sample_rate)`` samples, a
    partial last block dropped (conventions: Short Leq series and sound exposure; ADR 0170)."""
    p, fs = _level_powers(samples, sample_rate)
    d = real(duration, "duration")
    if not (math.isfinite(d) and d > 0):
        raise ValueError("duration must be finite and positive")
    n = math.floor(d * fs + 0.5)
    if n < 1:
        raise ValueError("duration * sample_rate must round to at least 1 sample")
    blocks = p.shape[0] // n
    return np.array(
        [float(np.mean(p[i * n : (i + 1) * n])) for i in range(blocks)], dtype=np.float64
    )


def sound_exposure(samples: ArrayLike, sample_rate: float) -> float:
    """The sound exposure ``sum |x|^2 / sample_rate`` (conventions: Short Leq series and sound
    exposure; ADR 0170)."""
    p, fs = _level_powers(samples, sample_rate)
    return float(np.sum(p)) / fs


def schroeder_decay(impulse_response: ArrayLike) -> NDArray[np.float64]:
    """The Schroeder backward-integrated energy decay ``10 log10(E[n]/E[0])``, ``E[n] =
    sum_{k >= n} |h[k]|^2`` (conventions: Reverberation time; ADR 0171)."""
    h = np.asarray(impulse_response)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError("impulse_response must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError("impulse_response must be finite")
    p = np.asarray(h.real * h.real + h.imag * h.imag, dtype=np.float64)
    energy = np.cumsum(p[::-1])[::-1]
    if not energy[0] > 0:
        raise ValueError("impulse_response must not be all zero")
    with np.errstate(divide="ignore"):
        return np.asarray(10 * np.log10(energy / energy[0]), dtype=np.float64)


def teager_energy(samples: ArrayLike) -> NDArray[np.float64]:
    """The Teager-Kaiser energy ``|x[n]|^2 - Re(x[n-1] conj x[n+1])``, ``N - 2`` values
    (conventions: Teager-Kaiser energy; ADR 0188)."""
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] < 3:
        raise ValueError("samples must be one-dimensional with at least three values")
    x = x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    mid = x[1:-1]
    cross = x[:-2] * np.conj(x[2:])
    return np.asarray(mid.real * mid.real + mid.imag * mid.imag - cross.real, dtype=np.float64)


def gcc_phat(
    x: ArrayLike, y: ArrayLike, sample_rate: float, *, max_delay: float | None = None
) -> GccPhat:
    """The delay of ``x`` relative to ``y`` from the phase-transform weighted cross-correlation
    (conventions: GCC-PHAT delay; ADR 0191)."""
    fs = real(sample_rate, "sample_rate")
    if not fs > 0:
        raise ValueError("sample_rate must be positive and finite")
    signals = []
    for v, what in ((x, "x"), (y, "y")):
        a = np.asarray(v)
        if a.ndim != 1 or a.shape[0] == 0 or np.iscomplexobj(a):
            raise ValueError(f"{what} must be a non-empty one-dimensional real array")
        a = a.astype(np.float64)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{what} must be finite")
        if not np.any(a != 0):
            raise ValueError(f"{what} must not be all zero")
        signals.append(a)
    n, m = signals[0].shape[0], signals[1].shape[0]
    lo, hi = -(m - 1), n - 1
    if max_delay is not None:
        md = real(max_delay, "max_delay")
        if md < 0:
            raise ValueError("max_delay must be at least 0")
        k = math.floor(md * fs)
        lo, hi = max(lo, -k), min(hi, k)
    size = n + m - 1
    g = np.fft.fft(signals[0], size) * np.conj(np.fft.fft(signals[1], size))
    mag = np.abs(g)
    w = np.where(mag > 0, g / np.where(mag > 0, mag, 1.0), 0.0)
    r = np.fft.ifft(w).real
    lags = np.arange(lo, hi + 1)
    vals = r[lags % size]
    best = int(np.argmax(vals))
    lag = int(lags[best])
    frac = 0.0
    if lo < lag < hi:
        a_, b_, c_ = float(vals[best - 1]), float(vals[best]), float(vals[best + 1])
        curve = a_ - 2 * b_ + c_
        if curve < 0:
            frac = (a_ - c_) / (2 * curve)
    return GccPhat((lag + frac) / fs, lag, float(vals[best]))


def energy_separation(samples: ArrayLike, sample_rate: float) -> EnergySeparation:
    """DESA-2 energy separation into instantaneous amplitude and frequency (conventions: Energy
    separation; ADR 0189)."""
    fs = real(sample_rate, "sample_rate")
    if not fs > 0:
        raise ValueError("sample_rate must be positive and finite")
    x = np.asarray(samples)
    if x.ndim != 1 or x.shape[0] < 5 or np.iscomplexobj(x):
        raise ValueError("samples must be one-dimensional and real with at least five values")
    x = x.astype(np.float64)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    px = x[2:-2] ** 2 - x[1:-3] * x[3:-1]
    y = x[2:] - x[:-2]
    py = y[1:-1] ** 2 - y[:-2] * y[2:]
    ok = (px > 0) & (py > 0)
    safe_px = np.where(ok, px, 1.0)
    safe_py = np.where(ok, py, 1.0)
    c = np.clip(1 - safe_py / (2 * safe_px), -1.0, 1.0)
    freq = np.where(ok, 0.5 * np.arccos(c) * (fs / (2 * math.pi)), math.nan)
    amp = np.where(ok, 2 * safe_px / np.sqrt(safe_py), math.nan)
    return EnergySeparation(np.asarray(amp, dtype=np.float64), np.asarray(freq, dtype=np.float64))


def energy_time_curve(impulse_response: ArrayLike) -> NDArray[np.float64]:
    """The energy-time curve ``10 log10(|z|^2 / max |z|^2)`` with ``z`` the analytic signal
    (conventions: Energy-time curve; ADR 0186)."""
    z = spectral.analytic_signal(impulse_response)
    p = np.asarray(z.real * z.real + z.imag * z.imag, dtype=np.float64)
    peak = float(np.max(p))
    if not peak > 0:
        raise ValueError("impulse_response must not be all zero")
    with np.errstate(divide="ignore"):
        return np.asarray(10 * np.log10(p / peak), dtype=np.float64)


def noise_compensated_decay(
    impulse_response: ArrayLike, *, tail: float = 0.1
) -> NDArray[np.float64]:
    """The Schroeder decay with the mean power of the last ``tail`` of the response subtracted
    before integrating, up to that noise window (conventions: Noise-compensated decay;
    ADR 0183)."""
    h = np.asarray(impulse_response)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError("impulse_response must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError("impulse_response must be finite")
    t = real(tail, "tail")
    if not (math.isfinite(t) and 0 < t < 1):
        raise ValueError("tail must be finite and in (0, 1)")
    n = h.shape[0]
    m = math.floor(t * n + 0.5)
    if not 1 <= m < n:
        raise ValueError("tail * length must round to between 1 and length - 1 samples")
    p = np.asarray(h.real * h.real + h.imag * h.imag, dtype=np.float64)
    noise = math.fsum(p[n - m :].tolist()) / m
    energy = np.cumsum((p[: n - m] - noise)[::-1])[::-1]
    if not energy[0] > 0:
        raise ValueError("impulse_response must have energy above the noise")
    out = np.full(n - m, -np.inf)
    above = energy > 0
    out[above] = 10 * np.log10(energy[above] / energy[0])
    return out


def reverberation_time(
    impulse_response: ArrayLike,
    sample_rate: float,
    *,
    start_db: float = -5.0,
    stop_db: float = -25.0,
) -> float:
    """The reverberation time ``-60/m`` from the least-squares slope ``m`` (dB/s) of the
    Schroeder decay between ``start_db`` and ``stop_db`` (conventions: Reverberation time;
    ADR 0171)."""
    return decay_time(
        schroeder_decay(impulse_response), sample_rate, start_db=start_db, stop_db=stop_db
    )


def decay_time(
    decay: ArrayLike,
    sample_rate: float,
    *,
    start_db: float = -5.0,
    stop_db: float = -25.0,
) -> float:
    """The decay time ``-60/m`` from the least-squares slope ``m`` (dB/s) of a supplied dB decay
    curve between ``start_db`` and ``stop_db`` (conventions: Decay time from a curve;
    ADR 0184)."""
    d = np.asarray(decay)
    if d.ndim != 1 or d.shape[0] == 0 or np.iscomplexobj(d):
        raise ValueError("decay must be a non-empty one-dimensional real array")
    d = d.astype(np.float64)
    if np.any(np.isnan(d) | (d == np.inf)):
        raise ValueError("decay must not hold NaN or +inf")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    a, b = real(start_db, "start_db"), real(stop_db, "stop_db")
    if not (math.isfinite(a) and math.isfinite(b) and b < a <= 0):
        raise ValueError("need stop_db < start_db <= 0, both finite")
    below_a = np.flatnonzero(d <= a)
    below_b = np.flatnonzero(d <= b)
    if below_b.shape[0] == 0:
        raise ValueError("the decay never reaches stop_db")
    n1, n2 = int(below_a[0]), int(below_b[0])
    if n2 - n1 < 2:
        raise ValueError("fewer than two samples lie between start_db and stop_db")
    n = np.arange(n1, n2, dtype=np.float64)
    y = d[n1:n2]
    nc = n - n.mean()
    slope = float(np.sum(nc * (y - y.mean())) / np.sum(nc * nc)) * fs
    if not slope < 0:
        raise ValueError("the decay slope must be negative")
    return -60.0 / slope


def early_decay_time(impulse_response: ArrayLike, sample_rate: float) -> float:
    """The early decay time: ``reverberation_time`` fitted from 0 to -10 dB (conventions: Early
    decay time; ADR 0181)."""
    return reverberation_time(impulse_response, sample_rate, start_db=0.0, stop_db=-10.0)


def decay_curvature(impulse_response: ArrayLike, sample_rate: float) -> float:
    """The decay curvature ``100 (T30/T20 - 1)`` in percent (conventions: Decay curvature;
    ADR 0182)."""
    t20 = reverberation_time(impulse_response, sample_rate, start_db=-5.0, stop_db=-25.0)
    t30 = reverberation_time(impulse_response, sample_rate, start_db=-5.0, stop_db=-35.0)
    return 100 * (t30 / t20 - 1)


def _early_late(
    impulse_response: ArrayLike, sample_rate: float, time: float
) -> tuple[float, float]:
    """The energies before and from sample ``round(time sample_rate)`` (conventions: Clarity and
    definition; ADR 0172)."""
    h = np.asarray(impulse_response)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError("impulse_response must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError("impulse_response must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    t = real(time, "time")
    if not (math.isfinite(t) and t > 0):
        raise ValueError("time must be finite and positive")
    n = math.floor(t * fs + 0.5)
    if n < 1:
        raise ValueError("time * sample_rate must round to at least 1 sample")
    p = h.real * h.real + h.imag * h.imag
    early, late = float(np.sum(p[:n])), float(np.sum(p[n:]))
    if not early + late > 0:
        raise ValueError("impulse_response must not be all zero")
    return early, late


def clarity(impulse_response: ArrayLike, sample_rate: float, *, time: float = 0.08) -> float:
    """The clarity ``10 log10(E_early/E_late)`` with the boundary at ``time`` seconds (C80 by
    default; conventions: Clarity and definition; ADR 0172)."""
    early, late = _early_late(impulse_response, sample_rate, time)
    if late == 0:
        return math.inf
    if early == 0:
        return -math.inf
    return 10 * math.log10(early / late)


def definition(impulse_response: ArrayLike, sample_rate: float, *, time: float = 0.05) -> float:
    """The definition ``E_early/E_total`` with the boundary at ``time`` seconds (D50 by default;
    conventions: Clarity and definition; ADR 0172)."""
    early, late = _early_late(impulse_response, sample_rate, time)
    return early / (early + late)


def centre_time(impulse_response: ArrayLike, sample_rate: float) -> float:
    """The centre time ``sum (n/fs)|h[n]|^2 / sum |h[n]|^2`` in seconds, from index 0
    (conventions: Centre time; ADR 0173)."""
    h = np.asarray(impulse_response)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError("impulse_response must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError("impulse_response must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    p = h.real * h.real + h.imag * h.imag
    total = float(np.sum(p))
    if not total > 0:
        raise ValueError("impulse_response must not be all zero")
    return float(np.sum(np.arange(p.shape[0], dtype=np.float64) * p)) / total / fs


def iacc(left: ArrayLike, right: ArrayLike, sample_rate: float, *, max_lag: float = 0.001) -> float:
    """The interaural cross-correlation ``max |sum l[n] r[n+t]| / sqrt(E_l E_r)`` over integer
    lags ``|t| <= round(max_lag sample_rate)`` (conventions: Interaural cross-correlation;
    ADR 0174)."""
    lt = np.asarray(left)
    rt = np.asarray(right)
    if lt.ndim != 1 or rt.ndim != 1 or lt.shape[0] == 0 or lt.shape != rt.shape:
        raise ValueError("left and right must be one-dimensional, non-empty and of equal length")
    if np.iscomplexobj(lt) or np.iscomplexobj(rt):
        raise ValueError("left and right must be real")
    lv = lt.astype(np.float64)
    rv = rt.astype(np.float64)
    if not (np.all(np.isfinite(lv)) and np.all(np.isfinite(rv))):
        raise ValueError("left and right must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    lag = real(max_lag, "max_lag")
    if not (math.isfinite(lag) and lag >= 0):
        raise ValueError("max_lag must be finite and non-negative")
    el, er = float(np.dot(lv, lv)), float(np.dot(rv, rv))
    if not (el > 0 and er > 0):
        raise ValueError("left and right must not be all zero")
    n = lv.shape[0]
    reach = min(math.floor(lag * fs + 0.5), n - 1)
    best = 0.0
    for t in range(-reach, reach + 1):
        r = float(np.dot(lv[: n - t], rv[t:])) if t >= 0 else float(np.dot(lv[-t:], rv[: n + t]))
        best = max(best, abs(r))
    return best / math.sqrt(el * er)


def lateral_fraction(
    omni: ArrayLike,
    figure_eight: ArrayLike,
    sample_rate: float,
    *,
    start: float = 0.005,
    stop: float = 0.08,
) -> float:
    """The lateral energy fraction ``sum_{Na <= n < Nb} h8^2 / sum_{n < Nb} ho^2`` (conventions:
    Lateral energy fraction; ADR 0175)."""
    o = np.asarray(omni)
    e = np.asarray(figure_eight)
    if o.ndim != 1 or e.ndim != 1 or o.shape[0] == 0 or o.shape != e.shape:
        raise ValueError(
            "omni and figure_eight must be one-dimensional, non-empty and of equal length"
        )
    if np.iscomplexobj(o) or np.iscomplexobj(e):
        raise ValueError("omni and figure_eight must be real")
    ov = o.astype(np.float64)
    ev = e.astype(np.float64)
    if not (np.all(np.isfinite(ov)) and np.all(np.isfinite(ev))):
        raise ValueError("omni and figure_eight must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    a = real(start, "start")
    b = real(stop, "stop")
    if not (math.isfinite(a) and math.isfinite(b) and 0 <= a < b):
        raise ValueError("start and stop must be finite with 0 <= start < stop")
    na = math.floor(a * fs + 0.5)
    nb = math.floor(b * fs + 0.5)
    if nb < 1:
        raise ValueError("stop * sample_rate must round to at least 1 sample")
    den = float(np.dot(ov[:nb], ov[:nb]))
    if not den > 0:
        raise ValueError("omni must have energy before stop")
    num = float(np.dot(ev[na:nb], ev[na:nb]))
    return num / den


def modulation_transfer(
    impulse_response: ArrayLike, sample_rate: float, frequencies: ArrayLike
) -> NDArray[np.float64]:
    """Schroeder's modulation transfer ``|sum |h[n]|^2 e^(-j 2 pi F n/fs)| / sum |h[n]|^2`` for
    each frequency (conventions: Modulation transfer function; ADR 0176)."""
    h = np.asarray(impulse_response)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError("impulse_response must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError("impulse_response must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    f = np.asarray(frequencies)
    if f.ndim != 1 or f.shape[0] == 0 or np.iscomplexobj(f):
        raise ValueError("frequencies must be a non-empty one-dimensional real array")
    fv = f.astype(np.float64)
    if not (np.all(np.isfinite(fv)) and np.all(fv >= 0)):
        raise ValueError("frequencies must be finite and non-negative")
    p = h.real * h.real + h.imag * h.imag
    total = float(np.sum(p))
    if not total > 0:
        raise ValueError("impulse_response must not be all zero")
    n = np.arange(p.shape[0], dtype=np.float64)
    out = np.empty(fv.shape[0], dtype=np.float64)
    for k, freq in enumerate(fv):
        phase = 2 * math.pi * float(freq) * n / fs
        out[k] = math.hypot(float(np.sum(p * np.cos(phase))), float(np.sum(p * np.sin(phase))))
    return out / total


_STI_ALPHA = (0.085, 0.127, 0.230, 0.233, 0.309, 0.224, 0.173)
_STI_BETA = (0.085, 0.078, 0.065, 0.011, 0.047, 0.095)


def _transmission_index(m: float) -> float:
    if m <= 0:
        return 0.0
    if m >= 1:
        return 1.0
    snr = min(max(10 * math.log10(m / (1 - m)), -15.0), 15.0)
    return (snr + 15) / 30


def speech_transmission_index(mtf: ArrayLike) -> float:
    """The STI of a 7-band MTF matrix with the IEC 60268-16:2020 male weights, without level,
    masking or threshold corrections (conventions: Speech transmission index; ADR 0177)."""
    try:
        m = np.asarray(mtf, dtype=np.float64)
    except (TypeError, ValueError):
        raise ValueError("mtf must be a 7-row matrix of real values") from None
    if m.ndim != 2 or m.shape[0] != 7 or m.shape[1] == 0:
        raise ValueError("mtf must have 7 rows and at least one column")
    if not np.all(np.isfinite(m)):
        raise ValueError("mtf must be finite")
    mti = [sum(_transmission_index(float(v)) for v in row) / m.shape[1] for row in m]
    sti = sum(a * t for a, t in zip(_STI_ALPHA, mti, strict=True))
    sti -= sum(b * math.sqrt(mti[k] * mti[k + 1]) for k, b in enumerate(_STI_BETA))
    return float(sti)


def _response_energy(x: ArrayLike, name: str) -> float:
    h = np.asarray(x)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError(f"{name} must be finite")
    return float(np.sum(h.real * h.real + h.imag * h.imag))


def sound_strength(impulse_response: ArrayLike, reference: ArrayLike) -> float:
    """The sound strength ``10 log10(sum |h|^2 / sum |h_ref|^2)`` in dB against the free-field
    response at 10 m (conventions: Sound strength; ADR 0178)."""
    energy = _response_energy(impulse_response, "impulse_response")
    ref = _response_energy(reference, "reference")
    if not ref > 0:
        raise ValueError("reference must not be all zero")
    if energy == 0:
        return -math.inf
    return 10 * math.log10(energy / ref)


def stage_support(impulse_response: ArrayLike, sample_rate: float, *, late: bool = False) -> float:
    """The stage support ``ST_early`` (20-100 ms) or ``ST_late`` (100-1000 ms) against the
    direct 0-10 ms, in dB (conventions: Stage support; ADR 0179)."""
    h = np.asarray(impulse_response)
    if h.ndim != 1 or h.shape[0] == 0:
        raise ValueError("impulse_response must be a non-empty one-dimensional array")
    h = h.astype(np.complex128 if np.iscomplexobj(h) else np.float64, copy=False)
    if not np.all(np.isfinite(h)):
        raise ValueError("impulse_response must be finite")
    fs = real(sample_rate, "sample_rate")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("sample_rate must be finite and positive")
    p = h.real * h.real + h.imag * h.imag

    def bound(t: float) -> int:
        return math.floor(t * fs + 0.5)

    direct_end = bound(0.01)
    if direct_end < 1:
        raise ValueError("sample_rate must give at least one direct-sound sample")
    direct = float(np.sum(p[:direct_end]))
    if not direct > 0:
        raise ValueError("impulse_response must have energy in the direct sound")
    a, b = (bound(0.1), bound(1.0)) if late else (bound(0.02), bound(0.1))
    window = float(np.sum(p[a:b]))
    if window == 0:
        return -math.inf
    return 10 * math.log10(window / direct)


def _band_times(times: ArrayLike) -> NDArray[np.float64]:
    t = np.asarray(times)
    if t.ndim != 1 or t.shape[0] != 6 or np.iscomplexobj(t):
        raise ValueError("times must be six real reverberation times (125 Hz to 4 kHz)")
    t = t.astype(np.float64)
    if not np.all(np.isfinite(t) & (t > 0)):
        raise ValueError("times must be finite and positive")
    return t


def bass_ratio(times: ArrayLike) -> float:
    """Beranek's bass ratio ``(T125 + T250)/(T500 + T1000)`` from the six octave-band times at
    125 Hz to 4 kHz (conventions: Bass and treble ratio; ADR 0180)."""
    t = _band_times(times)
    return float((t[0] + t[1]) / (t[2] + t[3]))


def treble_ratio(times: ArrayLike) -> float:
    """Beranek's treble ratio ``(T2000 + T4000)/(T500 + T1000)`` from the six octave-band times
    at 125 Hz to 4 kHz (conventions: Bass and treble ratio; ADR 0180)."""
    t = _band_times(times)
    return float((t[4] + t[5]) / (t[2] + t[3]))
