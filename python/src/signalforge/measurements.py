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
class LargestLyapunov:
    """Rosenstein's mean log divergence at each step and the exponent it gives, per sample
    (conventions: Largest Lyapunov exponent; ADR 0354)."""

    divergence: NDArray[np.float64]
    exponent: float


@dataclass(frozen=True)
class AggregatedVariance:
    """The variance of the block means at each size and the Hurst exponent they give
    (conventions: Aggregated variance; ADR 0355)."""

    sizes: NDArray[np.int64]
    values: NDArray[np.float64]
    hurst: float


@dataclass(frozen=True)
class TurningPoints:
    """The number of strict local extrema and its z-score against an i.i.d. record
    (conventions: Turning point test; ADR 0360)."""

    count: int
    z: float


@dataclass(frozen=True)
class RunsTest:
    """The number of runs above and below the mean and its z-score against a random record
    (conventions: Runs test; ADR 0361)."""

    runs: int
    z: float


@dataclass(frozen=True)
class BartelsRankTest:
    """The von Neumann ratio of the ranks and its z-score against a random record
    (conventions: Bartels rank test; ADR 0363)."""

    ratio: float
    z: float


@dataclass(frozen=True)
class MannKendall:
    """The Mann-Kendall statistic and its continuity-corrected z-score (conventions:
    Mann-Kendall trend test; ADR 0364)."""

    s: int
    z: float


@dataclass(frozen=True)
class Pettitt:
    """Pettitt's change-point statistic, where it is reached, and its approximate p-value
    (conventions: Pettitt change-point test; ADR 0366)."""

    statistic: int
    index: int
    p_value: float


@dataclass(frozen=True)
class BuishandRange:
    """Buishand's rescaled partial-sum maximum and range, and where the maximum is reached
    (conventions: Buishand range test; ADR 0367)."""

    q: float
    r: float
    index: int


@dataclass(frozen=True)
class Snht:
    """The standard normal homogeneity statistic and the last sample before the change
    (conventions: Standard normal homogeneity test; ADR 0368)."""

    statistic: float
    index: int


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


def auto_mutual_information(
    samples: ArrayLike, lags: Sequence[int], bins: int = 16
) -> NDArray[np.float64]:
    """Fraser and Swinney's auto mutual information: the mutual information in nats between
    ``x_t`` and ``x_{t+lag}`` from an equal-width histogram, at each lag (conventions: Auto
    mutual information; ADR 0352)."""
    nb = count(bins, "bins")
    if not 2 <= nb <= 4096:
        raise ValueError("bins must be from 2 to 4096")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    taus = [count(t, "lags") for t in lags]
    if len(taus) < 1:
        raise ValueError("lags must have at least one entry")
    if any(t > x.shape[0] - 1 for t in taus):
        raise ValueError("each lag must be at most len(samples) - 1")
    lo, hi = float(np.min(x)), float(np.max(x))
    if not hi > lo:
        raise ValueError("samples must not all be equal")
    b = np.minimum(nb - 1, np.floor((x - lo) * nb / (hi - lo)).astype(np.int64))
    out = np.empty(len(taus))
    for i, t in enumerate(taus):
        n = x.shape[0] - t
        first, second = b[:n], b[t:]
        ca = np.bincount(first, minlength=nb).astype(np.float64)
        cb = np.bincount(second, minlength=nb).astype(np.float64)
        joint = np.bincount(first * nb + second, minlength=nb * nb).astype(np.float64)
        ia, ib = np.divmod(np.flatnonzero(joint), nb)
        cab = joint[joint > 0]
        out[i] = float(np.sum(cab / n * np.log(cab * n / (ca[ia] * cb[ib]))))
    return out


def renyi_entropy(samples: ArrayLike, alpha: float, bins: int = 16) -> float:
    """The order-``alpha`` Rényi entropy in nats of an equal-width histogram of the samples,
    Shannon's at ``alpha = 1`` (conventions: Rényi entropy; ADR 0353)."""
    a = real(alpha, "alpha")
    if not a >= 0:
        raise ValueError("alpha must be at least 0")
    nb = count(bins, "bins")
    if not 2 <= nb <= 4096:
        raise ValueError("bins must be from 2 to 4096")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    lo, hi = float(np.min(x)), float(np.max(x))
    if not hi > lo:
        raise ValueError("samples must not all be equal")
    b = np.minimum(nb - 1, np.floor((x - lo) * nb / (hi - lo)).astype(np.int64))
    c = np.bincount(b)
    p = c[c > 0] / x.shape[0]
    if a == 0:
        return math.log(p.shape[0])
    if a == 1:
        return float(-np.sum(p * np.log(p)))
    return math.log(float(np.sum(p**a))) / (1 - a)


def largest_lyapunov(
    samples: ArrayLike, m: int, steps: int, delay: int = 1, theiler: int = 0
) -> LargestLyapunov:
    """Rosenstein's largest Lyapunov exponent: each embedded point's nearest neighbour outside
    the Theiler window, the mean log of their distance as both move on, and its least-squares
    slope (conventions: Largest Lyapunov exponent; ADR 0354)."""
    k = count(m, "m")
    big_k = count(steps, "steps")
    tau = count(delay, "delay")
    w = count(theiler, "theiler")
    if k < 1 or big_k < 1 or tau < 1:
        raise ValueError("m, steps and delay must be at least 1")
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
    windows = x.shape[0] - (k - 1) * tau
    p = windows - big_k
    if p < 2 * w + 2:
        raise ValueError("too few points: need N - (m - 1)*delay - steps >= 2*theiler + 2")
    emb = x[np.arange(windows)[:, None] + tau * np.arange(k)[None, :]]
    idx = np.arange(p)
    near = np.empty(p, dtype=np.int64)
    for j in range(p):
        d = np.max(np.abs(emb[:p] - emb[j]), axis=1)
        d[np.abs(idx - j) <= w] = np.inf
        near[j] = int(np.argmin(d))
    divergence = np.empty(big_k + 1)
    for s in range(big_k + 1):
        d = np.max(np.abs(emb[s : s + p] - emb[near + s]), axis=1)
        d = d[d > 0]
        if d.shape[0] == 0:
            raise ValueError("every pair has distance 0 at some step")
        divergence[s] = float(np.mean(np.log(d)))
    ks = np.arange(big_k + 1, dtype=np.float64)
    dx = ks - ks.mean()
    exponent = float(np.sum(dx * (divergence - divergence.mean())) / np.sum(dx * dx))
    return LargestLyapunov(divergence, exponent)


def aggregated_variance(samples: ArrayLike, sizes: Sequence[int]) -> AggregatedVariance:
    """The aggregated-variance Hurst estimator: the population variance of the means of
    non-overlapping blocks at each size, and ``1 + slope/2`` of its log-log line
    (conventions: Aggregated variance; ADR 0355)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    s = [count(v, "sizes") for v in sizes]
    if len(s) < 2:
        raise ValueError("sizes must have at least two entries")
    if any(s[i + 1] <= s[i] for i in range(len(s) - 1)):
        raise ValueError("sizes must be strictly increasing")
    if s[0] < 1 or 2 * s[-1] > x.shape[0]:
        raise ValueError("each size must be at least 1 and at most len(samples)/2")
    values = np.empty(len(s))
    for i, size in enumerate(s):
        blocks = x.shape[0] // size
        means = x[: blocks * size].reshape(blocks, size).mean(axis=1)
        values[i] = float(np.mean((means - means.mean()) ** 2))
    if not np.all(values > 0):
        raise ValueError("every size must have block means that vary")
    lx = np.log(np.array(s, dtype=np.float64))
    ly = np.log(values)
    dx = lx - lx.mean()
    beta = float(np.sum(dx * (ly - ly.mean())) / np.sum(dx * dx))
    return AggregatedVariance(np.array(s, dtype=np.int64), values, 1 + beta / 2)


def tsallis_entropy(samples: ArrayLike, q: float, bins: int = 16) -> float:
    """The order-``q`` Tsallis entropy of an equal-width histogram of the samples, Shannon's in
    nats at ``q = 1`` (conventions: Tsallis entropy; ADR 0356)."""
    a = real(q, "q")
    if not a >= 0:
        raise ValueError("q must be at least 0")
    nb = count(bins, "bins")
    if not 2 <= nb <= 4096:
        raise ValueError("bins must be from 2 to 4096")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    lo, hi = float(np.min(x)), float(np.max(x))
    if not hi > lo:
        raise ValueError("samples must not all be equal")
    b = np.minimum(nb - 1, np.floor((x - lo) * nb / (hi - lo)).astype(np.int64))
    c = np.bincount(b)
    p = c[c > 0] / x.shape[0]
    if a == 1:
        return float(-np.sum(p * np.log(p)))
    return (1 - float(np.sum(p**a))) / (a - 1)


def time_irreversibility(samples: ArrayLike, lag: int = 1) -> float:
    """The skewness of the lag increments, ``M3/(M2 sqrt(M2))``, a time-irreversibility
    statistic that is 0 on average for a reversible process (conventions: Time
    irreversibility; ADR 0357)."""
    tau = count(lag, "lag")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if not 1 <= tau <= x.shape[0] - 1:
        raise ValueError("lag must be from 1 to len(samples) - 1")
    d = x[tau:] - x[:-tau]
    m2 = float(np.mean(d * d))
    if not m2 > 0:
        raise ValueError("the increments must not all be 0")
    m3 = float(np.mean(d * d * d))
    return m3 / (m2 * math.sqrt(m2))


def cosine_similarity_entropy(samples: ArrayLike, m: int, r: float, delay: int = 1) -> float:
    """The binary Shannon entropy in bits of the share of embedded-vector pairs whose angular
    distance is below ``r`` (conventions: Cosine similarity entropy; ADR 0358)."""
    dim = count(m, "m")
    tau = count(delay, "delay")
    if dim < 1 or tau < 1:
        raise ValueError("m and delay must be at least 1")
    rr = real(r, "r")
    if not 0 < rr <= 1:
        raise ValueError("r must be above 0 and at most 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    w = x.shape[0] - (dim - 1) * tau
    if w < 2:
        raise ValueError("there must be at least two embedded vectors")
    v = np.stack([x[k * tau : k * tau + w] for k in range(dim)], axis=1)
    norms = np.sqrt(np.sum(v * v, axis=1))
    if not np.all(norms > 0):
        raise ValueError("no embedded vector may be all zeros")
    c = np.clip((v @ v.T) / np.outer(norms, norms), -1.0, 1.0)
    i, j = np.triu_indices(w, 1)
    b = int(np.count_nonzero(np.arccos(c[i, j]) / math.pi < rr)) / i.shape[0]
    if b in (0.0, 1.0):
        return 0.0
    return -b * math.log2(b) - (1 - b) * math.log2(1 - b)


def ljung_box(samples: ArrayLike, lags: int) -> float:
    """The Ljung-Box statistic ``N(N+2) sum rho_k^2/(N-k)`` over lags 1 to ``lags``
    (conventions: Ljung-Box statistic; ADR 0359)."""
    h = count(lags, "lags")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if not 1 <= h <= n - 1:
        raise ValueError("lags must be from 1 to len(samples) - 1")
    d = x - np.mean(x)
    c0 = float(np.dot(d, d))
    if not c0 > 0:
        raise ValueError("samples must not all be equal")
    q = 0.0
    for k in range(1, h + 1):
        rho = float(np.dot(d[:-k], d[k:])) / c0
        q += rho * rho / (n - k)
    return float(n * (n + 2)) * q


def turning_points(samples: ArrayLike) -> TurningPoints:
    """The turning point test: the number of samples strictly above or below both neighbours,
    and its z-score against the i.i.d. mean ``2(N-2)/3`` and variance ``(16N-29)/90``
    (conventions: Turning point test; ADR 0360)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 3:
        raise ValueError("samples must have at least 3 values")
    a, b, c = x[:-2], x[1:-1], x[2:]
    k = int(np.count_nonzero(((b > a) & (b > c)) | ((b < a) & (b < c))))
    z = (k - 2 * (n - 2) / 3) / math.sqrt((16 * n - 29) / 90)
    return TurningPoints(k, z)


def runs_test(samples: ArrayLike) -> RunsTest:
    """The Wald-Wolfowitz runs test about the mean: the number of runs of samples above and
    below it, those equal to it dropped, and the z-score of that number (conventions: Runs
    test; ADR 0361)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if x.shape[0] == 0:
        raise ValueError("samples must not be empty")
    mean = float(np.sum(x)) / x.shape[0]
    labels = x[x != mean] > mean
    n1 = int(np.count_nonzero(labels))
    n2 = labels.shape[0] - n1
    n = n1 + n2
    p = 2 * n1 * n2
    if not (n > 1 and p > n):
        raise ValueError("the runs variance must be above 0")
    runs = 1 + int(np.count_nonzero(labels[1:] != labels[:-1]))
    var = p * (p - n) / (n * n * (n - 1))
    return RunsTest(runs, (runs - p / n - 1) / math.sqrt(var))


def von_neumann_ratio(samples: ArrayLike) -> float:
    """The sum of squared successive differences over the sum of squared deviations from the
    mean, about 2 for an i.i.d. record (conventions: von Neumann ratio; ADR 0362)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    if x.shape[0] < 2:
        raise ValueError("samples must have at least 2 values")
    d = x - np.mean(x)
    den = float(np.dot(d, d))
    if not den > 0:
        raise ValueError("samples must not all be equal")
    s = np.diff(x)
    return float(np.dot(s, s)) / den


def bartels_rank_test(samples: ArrayLike) -> BartelsRankTest:
    """Bartels's rank test of randomness: the von Neumann ratio of the ranks, ties given their
    mean rank, and its z-score against 2 (conventions: Bartels rank test; ADR 0363)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 3:
        raise ValueError("samples must have at least 3 values")
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    if cnt.shape[0] < 2:
        raise ValueError("samples must not all be equal")
    start = np.cumsum(cnt) - cnt
    r = (start + (cnt + 1) / 2)[inv]
    d = r - (n + 1) / 2
    s = np.diff(r)
    ratio = float(np.dot(s, s)) / float(np.dot(d, d))
    var = 4 * (n - 2) * (5 * n * n - 2 * n - 9) / (5 * n * (n + 1) * (n - 1) ** 2)
    return BartelsRankTest(ratio, (ratio - 2) / math.sqrt(var))


def mann_kendall(samples: ArrayLike) -> MannKendall:
    """The Mann-Kendall trend test: ``S``, the number of rising pairs less the falling ones,
    and its tie-corrected, continuity-corrected z-score (conventions: Mann-Kendall trend test;
    ADR 0364)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    _, cnt = np.unique(x, return_counts=True)
    if cnt.shape[0] < 2:
        raise ValueError("samples must not all be equal")
    s = 0
    for i in range(n - 1):
        s += int(np.count_nonzero(x[i + 1 :] > x[i])) - int(np.count_nonzero(x[i + 1 :] < x[i]))
    t = [int(c) for c in cnt]
    var = (n * (n - 1) * (2 * n + 5) - sum(c * (c - 1) * (2 * c + 5) for c in t)) / 18
    z = 0.0 if s == 0 else (s - 1 if s > 0 else s + 1) / math.sqrt(var)
    return MannKendall(s, z)


def sens_slope(samples: ArrayLike) -> float:
    """Sen's slope: the median of the slopes ``(x_j - x_i)/(j - i)`` over every pair
    ``i < j``, per sample (conventions: Sen's slope; ADR 0365)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    i, j = np.triu_indices(n, 1)
    s = np.sort((x[j] - x[i]) / (j - i))
    k = s.shape[0]
    if k % 2:
        return float(s[k // 2])
    return (float(s[k // 2 - 1]) + float(s[k // 2])) / 2


def pettitt(samples: ArrayLike) -> Pettitt:
    """Pettitt's change-point test: the largest ``|U_t|`` over the splits, the last sample
    before the change, and the approximate p-value (conventions: Pettitt change-point test;
    ADR 0366)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    u = 0
    best, where = -1, 0
    for t in range(n - 1):
        u += int(np.count_nonzero(x > x[t])) - int(np.count_nonzero(x < x[t]))
        if abs(u) > best:
            best, where = abs(u), t
    p = min(1.0, 2 * math.exp(-6 * best * best / (n**3 + n**2)))
    return Pettitt(best, where, p)


def buishand_range(samples: ArrayLike) -> BuishandRange:
    """Buishand's range test: the partial sums of the deviations from the mean, their largest
    size and their range over the population standard deviation, and the last sample before
    the change (conventions: Buishand range test; ADR 0367)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    d = x - float(np.sum(x)) / n
    var = float(np.dot(d, d)) / n
    if not var > 0:
        raise ValueError("samples must not all be equal")
    sigma = math.sqrt(var)
    s = np.cumsum(d)
    index = int(np.argmax(np.abs(s)))
    hi = max(0.0, float(np.max(s)))
    lo = min(0.0, float(np.min(s)))
    return BuishandRange(abs(float(s[index])) / sigma, (hi - lo) / sigma, index)


def snht(samples: ArrayLike) -> Snht:
    """Alexandersson's standard normal homogeneity test: the largest ``T_k`` over the splits,
    and the last sample before the change (conventions: Standard normal homogeneity test;
    ADR 0368)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    d = x - float(np.sum(x)) / n
    var = float(np.dot(d, d)) / n
    if not var > 0:
        raise ValueError("samples must not all be equal")
    s = np.cumsum(d)[:-1]
    k = np.arange(1, n, dtype=np.float64)
    t = n * s * s / (k * (n - k) * var)
    index = int(np.argmax(t))
    return Snht(float(t[index]), index)


def _mean_ranks(x: NDArray[np.float64]) -> NDArray[np.float64]:
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    start = np.cumsum(cnt) - cnt
    r: NDArray[np.float64] = (start + (cnt + 1) / 2)[inv].astype(np.float64)
    return r


def spearman_correlation(x: ArrayLike, y: ArrayLike) -> float:
    """Spearman's rank correlation: the Pearson correlation of the ranks of ``x`` and ``y``,
    ties given their mean rank (conventions: Spearman rank correlation; ADR 0369)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 2:
        raise ValueError("x and y must have at least 2 values")
    if a.min() == a.max() or b.min() == b.max():
        raise ValueError("neither x nor y may have every value equal")
    c = (n + 1) / 2
    r = _mean_ranks(a) - c
    s = _mean_ranks(b) - c
    return float(np.dot(r, s)) / math.sqrt(float(np.dot(r, r)) * float(np.dot(s, s)))


def kendall_tau(x: ArrayLike, y: ArrayLike) -> float:
    """Kendall's tau-b: the concordant pairs less the discordant ones, over the tie-corrected
    count of pairs (conventions: Kendall's tau-b; ADR 0370)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 2:
        raise ValueError("x and y must have at least 2 values")
    if a.min() == a.max() or b.min() == b.max():
        raise ValueError("neither x nor y may have every value equal")
    i, j = np.triu_indices(n, 1)
    s = int(np.sum(np.sign(a[j] - a[i]).astype(np.int64) * np.sign(b[j] - b[i]).astype(np.int64)))
    n0 = n * (n - 1) // 2
    ties = []
    for v in (a, b):
        _, cnt = np.unique(v, return_counts=True)
        ties.append(int(np.sum(cnt * (cnt - 1) // 2)))
    return s / math.sqrt(float(n0 - ties[0]) * float(n0 - ties[1]))


def pearson_correlation(x: ArrayLike, y: ArrayLike) -> float:
    """The Pearson product-moment correlation of ``x`` and ``y`` (conventions: Pearson
    correlation; ADR 0371)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 2:
        raise ValueError("x and y must have at least 2 values")
    if a.min() == a.max() or b.min() == b.max():
        raise ValueError("neither x nor y may have every value equal")
    u = a - float(np.sum(a)) / n
    w = b - float(np.sum(b)) / n
    return float(np.dot(u, w)) / math.sqrt(float(np.dot(u, u)) * float(np.dot(w, w)))


def _double_centred(v: NDArray[np.float64]) -> NDArray[np.float64]:
    a = np.abs(v[:, None] - v[None, :])
    m = a.mean(axis=1)
    out: NDArray[np.float64] = a - m[:, None] - m[None, :] + float(m.mean())
    return out


def distance_correlation(x: ArrayLike, y: ArrayLike) -> float:
    """The distance correlation of ``x`` and ``y``, from the double-centred distance matrices,
    0 only for independent records (conventions: Distance correlation; ADR 0372)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 2:
        raise ValueError("x and y must have at least 2 values")
    if a.min() == a.max() or b.min() == b.max():
        raise ValueError("neither x nor y may have every value equal")
    big_a = _double_centred(a)
    big_b = _double_centred(b)
    nn = float(n) * n
    cov = float(np.sum(big_a * big_b)) / nn
    va = float(np.sum(big_a * big_a)) / nn
    vb = float(np.sum(big_b * big_b)) / nn
    return math.sqrt(max(0.0, cov) / math.sqrt(va * vb))


def _biweight_terms(v: NDArray[np.float64], name: str) -> NDArray[np.float64]:
    m = float(np.median(v))
    d = v - m
    mad = float(np.median(np.abs(d)))
    if not mad > 0:
        raise ValueError(f"{name} must have a nonzero median absolute deviation")
    u = d / (9 * mad)
    w = np.where(np.abs(u) < 1, (1 - u * u) * (1 - u * u), 0.0)
    out: NDArray[np.float64] = d * w
    return out


def biweight_midcorrelation(x: ArrayLike, y: ArrayLike) -> float:
    """The biweight midcorrelation of ``x`` and ``y``: a correlation of the deviations from
    the medians, weighted by Tukey's biweight in units of ``9 MAD`` (conventions: Biweight
    midcorrelation; ADR 0373)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 2:
        raise ValueError("x and y must have at least 2 values")
    p = _biweight_terms(a, "x")
    q = _biweight_terms(b, "y")
    return float(np.dot(p, q)) / math.sqrt(float(np.dot(p, p)) * float(np.dot(q, q)))


def hoeffding_d(x: ArrayLike, y: ArrayLike) -> float:
    """Hoeffding's D: a rank statistic of dependence of any shape, 1 for a monotone pair
    without ties and about 0 for independent ones (conventions: Hoeffding's D; ADR 0374)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 5:
        raise ValueError("x and y must have at least 5 values")
    r = _mean_ranks(a)
    s = _mean_ranks(b)
    fa = np.where(a[:, None] < a[None, :], 1.0, np.where(a[:, None] == a[None, :], 0.5, 0.0))
    fb = np.where(b[:, None] < b[None, :], 1.0, np.where(b[:, None] == b[None, :], 0.5, 0.0))
    # Column i sums over j; the diagonal j = i is 1/2 * 1/2 and is taken back out.
    q = 1 + np.sum(fa * fb, axis=0) - 0.25
    d1 = float(np.sum((q - 1) * (q - 2)))
    d2 = float(np.sum((r - 1) * (r - 2) * (s - 1) * (s - 2)))
    d3 = float(np.sum((r - 2) * (s - 2) * (q - 1)))
    nf = float(n)
    top = (nf - 2) * (nf - 3) * d1 + d2 - 2 * (nf - 2) * d3
    return 30 * top / (nf * (nf - 1) * (nf - 2) * (nf - 3) * (nf - 4))


def blomqvist_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Blomqvist's beta, the medial correlation: the share of samples on the same side of both
    medians less the share on opposite sides, samples on a median dropped (conventions:
    Blomqvist's beta; ADR 0375)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n == 0:
        raise ValueError("x and y must not be empty")
    signs = []
    for v in (a, b):
        s = np.sort(v)
        k = n // 2
        med = s[k] if n % 2 == 1 else (s[k - 1] + s[k]) / 2
        signs.append(np.sign(v - med))
    p = signs[0] * signs[1]
    agree = int(np.count_nonzero(p > 0))
    disagree = int(np.count_nonzero(p < 0))
    if agree + disagree == 0:
        raise ValueError("every sample lies on a median")
    return (agree - disagree) / (agree + disagree)


def chatterjee_xi(x: ArrayLike, y: ArrayLike) -> float:
    """Chatterjee's xi: how well ``x`` predicts ``y``, near 0 for independent records and near 1
    when ``y`` is a function of ``x`` (conventions: Chatterjee's xi; ADR 0376)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    if n < 2:
        raise ValueError("x and y must have at least 2 values")
    ys = b[np.argsort(a, kind="stable")]
    sy = np.sort(b)
    r = np.searchsorted(sy, ys, side="right").astype(np.int64)
    left = n - np.searchsorted(sy, ys, side="left").astype(np.int64)
    s = int(np.sum(np.abs(np.diff(r))))
    t = int(np.sum(left * (n - left)))
    if t == 0:
        raise ValueError("y must not be constant")
    return float(1 - (n * s) / (2 * t))


def goodman_kruskal_gamma(x: ArrayLike, y: ArrayLike) -> float:
    """Goodman and Kruskal's gamma: concordant less discordant pairs over their sum, pairs tied
    in either record dropped (conventions: Goodman and Kruskal's gamma; ADR 0377)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    sa = (a[:, None] > a[None, :]).astype(np.int8) - (a[:, None] < a[None, :])
    sb = (b[:, None] > b[None, :]).astype(np.int8) - (b[:, None] < b[None, :])
    p = sa * sb
    # The full matrix holds every pair twice.
    concordant = int(np.count_nonzero(p > 0)) // 2
    discordant = int(np.count_nonzero(p < 0)) // 2
    if concordant + discordant == 0:
        raise ValueError("no pair is untied in both x and y")
    return (concordant - discordant) / (concordant + discordant)


def somers_d(x: ArrayLike, y: ArrayLike) -> float:
    """Somers' D, ``d_yx``: concordant less discordant pairs over the pairs untied in ``x``,
    for predicting ``y`` from ``x`` (conventions: Somers' D; ADR 0378)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    a, b = pair
    n = a.shape[0]
    if b.shape[0] != n:
        raise ValueError("x and y must be the same length")
    sa = (a[:, None] > a[None, :]).astype(np.int8) - (a[:, None] < a[None, :])
    sb = (b[:, None] > b[None, :]).astype(np.int8) - (b[:, None] < b[None, :])
    p = sa * sb
    # The full matrix holds every pair twice.
    concordant = int(np.count_nonzero(p > 0)) // 2
    discordant = int(np.count_nonzero(p < 0)) // 2
    # The diagonal is tied with itself; the rest of the zeros are each pair twice.
    untied = n * (n - 1) // 2 - (int(np.count_nonzero(sa == 0)) - n) // 2
    if untied == 0:
        raise ValueError("no pair is untied in x")
    return float((concordant - discordant) / untied)


def kendall_w(ratings: ArrayLike) -> float:
    """Kendall's W, the coefficient of concordance: how well the raters in the rows of
    ``ratings`` agree on the order of the items in its columns, from 0 to 1 (conventions:
    Kendall's W; ADR 0379)."""
    a = np.asarray(ratings)
    if a.ndim != 2:
        raise ValueError("ratings must be two-dimensional")
    if np.iscomplexobj(a):
        raise ValueError("ratings must be real")
    try:
        a = a.astype(np.float64, copy=False)
    except (TypeError, ValueError):
        raise ValueError("ratings must be real numbers") from None
    if not np.all(np.isfinite(a)):
        raise ValueError("ratings must be finite")
    m, n = int(a.shape[0]), int(a.shape[1])
    if m < 2:
        raise ValueError("ratings must have at least 2 raters (rows)")
    if n < 2:
        raise ValueError("ratings must have at least 2 items (columns)")
    rank_sums = np.zeros(n)
    ties = 0
    for row in a:
        rank_sums += _mean_ranks(row)
        counts = np.unique(row, return_counts=True)[1].astype(np.int64)
        ties += int(np.sum(counts**3 - counts))
    s = float(np.sum((rank_sums - m * (n + 1) / 2) ** 2))
    denominator = m * m * (n**3 - n) - m * ties
    if denominator == 0:
        raise ValueError("every rater gives every item the same value")
    return 12 * s / denominator


def cronbach_alpha(scores: ArrayLike) -> float:
    """Cronbach's alpha: the internal consistency of the items in the rows of ``scores`` over
    the subjects in its columns, at most 1 (conventions: Cronbach's alpha; ADR 0380)."""
    a = np.asarray(scores)
    if a.ndim != 2:
        raise ValueError("scores must be two-dimensional")
    if np.iscomplexobj(a):
        raise ValueError("scores must be real")
    try:
        a = a.astype(np.float64, copy=False)
    except (TypeError, ValueError):
        raise ValueError("scores must be real numbers") from None
    if not np.all(np.isfinite(a)):
        raise ValueError("scores must be finite")
    k, n = int(a.shape[0]), int(a.shape[1])
    if k < 2:
        raise ValueError("scores must have at least 2 items (rows)")
    if n < 2:
        raise ValueError("scores must have at least 2 subjects (columns)")
    items = float(np.sum(np.var(a, axis=1, ddof=1)))
    total = float(np.var(np.sum(a, axis=0), ddof=1))
    if total == 0:
        raise ValueError("the subject totals must not all be equal")
    return k / (k - 1) * (1 - items / total)


def icc_consistency(ratings: ArrayLike) -> float:
    """The intraclass correlation ICC(3,1): the two-way consistency of a single rating, raters
    in the rows of ``ratings`` and subjects in its columns (conventions: ICC(3,1); ADR 0381)."""
    a = np.asarray(ratings)
    if a.ndim != 2:
        raise ValueError("ratings must be two-dimensional")
    if np.iscomplexobj(a):
        raise ValueError("ratings must be real")
    try:
        a = a.astype(np.float64, copy=False)
    except (TypeError, ValueError):
        raise ValueError("ratings must be real numbers") from None
    if not np.all(np.isfinite(a)):
        raise ValueError("ratings must be finite")
    k, n = int(a.shape[0]), int(a.shape[1])
    if k < 2:
        raise ValueError("ratings must have at least 2 raters (rows)")
    if n < 2:
        raise ValueError("ratings must have at least 2 subjects (columns)")
    grand = float(np.mean(a))
    rows = np.mean(a, axis=1)
    cols = np.mean(a, axis=0)
    ms_s = k * float(np.sum((cols - grand) ** 2)) / (n - 1)
    residual = a - rows[:, None] - cols[None, :] + grand
    ms_e = float(np.sum(residual**2)) / ((n - 1) * (k - 1))
    denominator = ms_s + (k - 1) * ms_e
    if denominator == 0:
        raise ValueError("the subjects do not differ once the rater offsets are removed")
    return (ms_s - ms_e) / denominator


def fleiss_kappa(counts: ArrayLike) -> float:
    """Fleiss' kappa: the chance-corrected agreement of raters who each put every subject in
    one category, from ``counts[subject, category]`` (conventions: Fleiss' kappa; ADR 0382)."""
    a = np.asarray(counts)
    if a.ndim != 2:
        raise ValueError("counts must be two-dimensional")
    if np.iscomplexobj(a):
        raise ValueError("counts must be real")
    try:
        a = a.astype(np.float64, copy=False)
    except (TypeError, ValueError):
        raise ValueError("counts must be real numbers") from None
    if not np.all(np.isfinite(a)):
        raise ValueError("counts must be finite")
    if np.any(a < 0) or np.any(a != np.floor(a)):
        raise ValueError("counts must be whole numbers, not negative")
    subjects, categories = int(a.shape[0]), int(a.shape[1])
    if subjects < 1:
        raise ValueError("counts must have at least 1 subject (row)")
    if categories < 2:
        raise ValueError("counts must have at least 2 categories (columns)")
    sums = np.sum(a, axis=1)
    n = float(sums[0])
    if np.any(sums != n):
        raise ValueError("every subject must have the same number of ratings")
    if n < 2:
        raise ValueError("every subject must have at least 2 ratings")
    p = np.sum(a, axis=0) / (subjects * n)
    expected = float(np.sum(p**2))
    if expected == 1:
        raise ValueError("every rating is in the same category")
    observed = float(np.mean((np.sum(a**2, axis=1) - n) / (n * (n - 1))))
    return (observed - expected) / (1 - expected)


def cohen_kappa(a: ArrayLike, b: ArrayLike) -> float:
    """Cohen's kappa: the chance-corrected agreement of two raters' labels ``a`` and ``b`` of
    the same items (conventions: Cohen's kappa; ADR 0383)."""
    pair = []
    for name, v in (("a", a), ("b", b)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all(np.isfinite(r)):
            raise ValueError(f"{name} must be finite")
        pair.append(r)
    x, y = pair
    if x.size != y.size:
        raise ValueError("a and b must be the same length")
    if x.size < 1:
        raise ValueError("a and b must not be empty")
    n = int(x.size)
    agree = int(np.count_nonzero(x == y))
    labels, codes = np.unique(np.concatenate([x, y]), return_inverse=True)
    ca = np.bincount(codes[:n], minlength=labels.size).astype(np.int64)
    cb = np.bincount(codes[n:], minlength=labels.size).astype(np.int64)
    chance = int(np.sum(ca * cb))
    if chance == n * n:
        raise ValueError("both raters give every item the same label")
    return float((n * agree - chance) / (n * n - chance))


def scott_pi(a: ArrayLike, b: ArrayLike) -> float:
    """Scott's pi: the agreement of two raters' labels ``a`` and ``b`` of the same items,
    corrected for chance from their pooled label rates (conventions: Scott's pi; ADR 0384)."""
    pair = []
    for name, v in (("a", a), ("b", b)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all(np.isfinite(r)):
            raise ValueError(f"{name} must be finite")
        pair.append(r)
    x, y = pair
    if x.size != y.size:
        raise ValueError("a and b must be the same length")
    if x.size < 1:
        raise ValueError("a and b must not be empty")
    n = int(x.size)
    agree = int(np.count_nonzero(x == y))
    counts = np.unique(np.concatenate([x, y]), return_counts=True)[1].astype(np.int64)
    pooled = int(np.sum(counts**2))
    if pooled == 4 * n * n:
        raise ValueError("every label in both records is the same")
    return float((4 * n * agree - pooled) / (4 * n * n - pooled))


def matthews_correlation(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Matthews correlation coefficient of a binary ``decision`` against the ``truth``,
    both records of 0 and 1, from -1 to 1 (conventions: Matthews correlation; ADR 0385)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    tn = int(np.count_nonzero(~t & ~d))
    fp = int(np.count_nonzero(~t & d))
    fn = int(np.count_nonzero(t & ~d))
    product = float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if product == 0:
        raise ValueError("both classes must appear in both truth and decision")
    return (tp * tn - fp * fn) / math.sqrt(product)


def f1_score(truth: ArrayLike, decision: ArrayLike) -> float:
    """The F1 score of a binary ``decision`` against the ``truth``, both records of 0 and 1:
    the harmonic mean of precision and recall, from 0 to 1 (conventions: F1 score;
    ADR 0386)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    wrong = int(np.count_nonzero(t != d))
    if 2 * tp + wrong == 0:
        raise ValueError("truth or decision must hold at least one positive")
    return 2 * tp / (2 * tp + wrong)


def youden_j(truth: ArrayLike, decision: ArrayLike) -> float:
    """Youden's J of a binary ``decision`` against the ``truth``, both records of 0 and 1:
    sensitivity plus specificity less 1, from -1 to 1 (conventions: Youden's J; ADR 0387)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    tn = int(np.count_nonzero(~t & ~d))
    fp = int(np.count_nonzero(~t & d))
    fn = int(np.count_nonzero(t & ~d))
    if tp + fn == 0 or tn + fp == 0:
        raise ValueError("both classes must appear in the truth")
    return (tp * tn - fp * fn) / ((tp + fn) * (tn + fp))


def jaccard_index(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Jaccard index of two binary records of 0 and 1: the items both mark 1 over the
    items either marks 1, from 0 to 1 (conventions: Jaccard index; ADR 0388)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    either = int(np.count_nonzero(t | d))
    if either == 0:
        raise ValueError("truth or decision must hold at least one 1")
    return both / either


def fowlkes_mallows_index(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Fowlkes-Mallows index of a binary ``decision`` against the ``truth``, both records
    of 0 and 1: the geometric mean of precision and recall, from 0 to 1 (conventions:
    Fowlkes-Mallows index; ADR 0389)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    decided = int(np.count_nonzero(d))
    actual = int(np.count_nonzero(t))
    if decided == 0 or actual == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return tp / math.sqrt(float(decided) * actual)


def diagnostic_odds_ratio(truth: ArrayLike, decision: ArrayLike) -> float:
    """The diagnostic odds ratio of a binary ``decision`` against the ``truth``, both records
    of 0 and 1: ``(TP*TN)/(FP*FN)`` (conventions: Diagnostic odds ratio; ADR 0390)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    tn = int(np.count_nonzero(~t & ~d))
    fp = int(np.count_nonzero(~t & d))
    fn = int(np.count_nonzero(t & ~d))
    if fp == 0 or fn == 0:
        raise ValueError("the ratio needs at least one false positive and one false negative")
    return float(tp * tn) / float(fp * fn)


def brier_score(outcome: ArrayLike, probability: ArrayLike) -> float:
    """The Brier score of the forecast ``probability`` of a binary event against the
    ``outcome``, 0 or 1: the mean squared difference, from 0 to 1 (conventions: Brier score;
    ADR 0391)."""
    y = np.asarray(outcome)
    p = np.asarray(probability)
    for name, r in (("outcome", y), ("probability", p)):
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
    y = y.astype(np.float64, copy=False)
    p = p.astype(np.float64, copy=False)
    if y.size != p.size:
        raise ValueError("outcome and probability must be the same length")
    if y.size < 1:
        raise ValueError("outcome and probability must not be empty")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("outcome must hold only 0 and 1")
    if not np.all((p >= 0) & (p <= 1)):
        raise ValueError("probability must be in [0, 1]")
    total = 0.0
    for pi, yi in zip(p.tolist(), y.tolist(), strict=True):
        total += (pi - yi) * (pi - yi)
    return total / y.size


def log_loss(outcome: ArrayLike, probability: ArrayLike) -> float:
    """The log loss of the forecast ``probability`` of a binary event against the
    ``outcome``, 0 or 1: the negative mean natural log-likelihood, in nats (conventions: Log
    loss; ADR 0392)."""
    y = np.asarray(outcome)
    p = np.asarray(probability)
    for name, r in (("outcome", y), ("probability", p)):
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
    y = y.astype(np.float64, copy=False)
    p = p.astype(np.float64, copy=False)
    if y.size != p.size:
        raise ValueError("outcome and probability must be the same length")
    if y.size < 1:
        raise ValueError("outcome and probability must not be empty")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("outcome must hold only 0 and 1")
    if not np.all((p >= 0) & (p <= 1)):
        raise ValueError("probability must be in [0, 1]")
    total = 0.0
    for pi, yi in zip(p.tolist(), y.tolist(), strict=True):
        q = pi if yi == 1 else 1.0 - pi
        if q == 0:
            raise ValueError("a forecast of certainty was wrong: the loss is infinite")
        total += math.log(q)
    return -total / y.size


def roc_auc(truth: ArrayLike, score: ArrayLike) -> float:
    """The area under the ROC curve of a real ``score`` against the binary ``truth``: the
    share of positive-negative pairs where the positive scores higher, ties counting half
    (conventions: ROC AUC; ADR 0393)."""
    t = np.asarray(truth)
    s = np.asarray(score)
    for name, r in (("truth", t), ("score", s)):
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
    t = t.astype(np.float64, copy=False)
    s = s.astype(np.float64, copy=False)
    if t.size != s.size:
        raise ValueError("truth and score must be the same length")
    if not np.all((t == 0) | (t == 1)):
        raise ValueError("truth must hold only 0 and 1")
    if not np.all(np.isfinite(s)):
        raise ValueError("score must be finite")
    pos = t == 1
    n1 = int(np.count_nonzero(pos))
    n0 = t.size - n1
    if n1 == 0 or n0 == 0:
        raise ValueError("truth must hold at least one 0 and one 1")
    r1 = float(np.sum(_mean_ranks(s)[pos]))
    return (r1 - n1 * (n1 + 1) / 2) / (float(n1) * n0)


def average_precision(truth: ArrayLike, score: ArrayLike) -> float:
    """The average precision of a real ``score`` against the binary ``truth``: the precision
    at each distinct score, weighted by the positives first reached there (conventions:
    Average precision; ADR 0394)."""
    t = np.asarray(truth)
    s = np.asarray(score)
    for name, r in (("truth", t), ("score", s)):
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
    t = t.astype(np.float64, copy=False)
    s = s.astype(np.float64, copy=False)
    if t.size != s.size:
        raise ValueError("truth and score must be the same length")
    if not np.all((t == 0) | (t == 1)):
        raise ValueError("truth must hold only 0 and 1")
    if not np.all(np.isfinite(s)):
        raise ValueError("score must be finite")
    n1 = int(np.count_nonzero(t == 1))
    if n1 == 0:
        raise ValueError("truth must hold at least one 1")
    order = np.argsort(-s, kind="stable")
    ss = s[order].tolist()
    tt = t[order].tolist()
    total = 0.0
    seen = hits = 0
    i = 0
    while i < len(ss):
        k = 0
        j = i
        while j < len(ss) and ss[j] == ss[i]:
            k += int(tt[j] == 1)
            j += 1
        seen = j
        hits += k
        if k:
            total += float(k * hits) / seen
        i = j
    return total / n1


def markedness(truth: ArrayLike, decision: ArrayLike) -> float:
    """Markedness of a binary ``decision`` against the ``truth``, both records of 0 and 1: the
    precision and the negative predictive value less 1, from -1 to 1 (conventions:
    Markedness; ADR 0395)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    tn = int(np.count_nonzero(~t & ~d))
    fp = int(np.count_nonzero(~t & d))
    fn = int(np.count_nonzero(t & ~d))
    if tp + fp == 0 or tn + fn == 0:
        raise ValueError("decision must hold at least one 0 and one 1")
    return float(tp * tn - fp * fn) / float((tp + fp) * (tn + fn))


def balanced_accuracy(truth: ArrayLike, decision: ArrayLike) -> float:
    """The balanced accuracy of a binary ``decision`` against the ``truth``, both records of
    0 and 1: the mean of the sensitivity and the specificity, from 0 to 1 (conventions:
    Balanced accuracy; ADR 0396)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    tn = int(np.count_nonzero(~t & ~d))
    fp = int(np.count_nonzero(~t & d))
    fn = int(np.count_nonzero(t & ~d))
    if tp + fn == 0 or tn + fp == 0:
        raise ValueError("truth must hold at least one 0 and one 1")
    return float(tp * (tn + fp) + tn * (tp + fn)) / float(2 * (tp + fn) * (tn + fp))


def cohen_d(x: ArrayLike, y: ArrayLike) -> float:
    """Cohen's d: the difference of the means of ``x`` and ``y`` over their pooled standard
    deviation, positive when ``x`` has the larger mean (conventions: Cohen's d; ADR 0397)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 2:
            raise ValueError(f"{name} must hold at least 2 values")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a.tolist())
    means = []
    ss = 0.0
    for values in pair:
        total = 0.0
        for v in values:
            total += v
        mean = total / len(values)
        for v in values:
            ss += (v - mean) * (v - mean)
        means.append(mean)
    s = math.sqrt(ss / (len(pair[0]) + len(pair[1]) - 2))
    if s == 0:
        raise ValueError("the pooled standard deviation is zero")
    return (means[0] - means[1]) / s


def hedges_g(x: ArrayLike, y: ArrayLike) -> float:
    """Hedges' g: Cohen's d of ``x`` and ``y`` times the exact small-sample correction
    ``J(m) = Gamma(m/2)/(sqrt(m/2) Gamma((m-1)/2))``, ``m = n_x + n_y - 2`` (conventions:
    Hedges' g; ADR 0398)."""
    d = cohen_d(x, y)
    m = np.asarray(x).size + np.asarray(y).size - 2
    j = math.exp(math.lgamma(m / 2) - math.lgamma((m - 1) / 2)) / math.sqrt(m / 2)
    return j * d


def glass_delta(x: ArrayLike, y: ArrayLike) -> float:
    """Glass's delta: the difference of the means of the treated sample ``x`` and the control
    ``y`` over the control's sample standard deviation (conventions: Glass's delta;
    ADR 0399)."""
    pair = []
    for name, v, least in (("x", x, 1), ("y", y, 2)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < least:
            raise ValueError(f"{name} must hold at least {least} values")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a.tolist())
    means = []
    for values in pair:
        total = 0.0
        for v in values:
            total += v
        means.append(total / len(values))
    ss = 0.0
    for v in pair[1]:
        ss += (v - means[1]) * (v - means[1])
    s = math.sqrt(ss / (len(pair[1]) - 1))
    if s == 0:
        raise ValueError("the control's standard deviation is zero")
    return (means[0] - means[1]) / s


def cliff_delta(x: ArrayLike, y: ArrayLike) -> float:
    """Cliff's delta: over every pair of a value of ``x`` and one of ``y``, the share where
    ``x`` is larger less the share where it is smaller, from -1 to 1 (conventions: Cliff's
    delta; ADR 0400)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    xs, ys = pair[0], np.sort(pair[1])
    below = int(np.sum(np.searchsorted(ys, xs, side="left")))
    above = int(np.sum(ys.size - np.searchsorted(ys, xs, side="right")))
    return float(below - above) / float(xs.size * ys.size)


def vargha_delaney_a(x: ArrayLike, y: ArrayLike) -> float:
    """The Vargha-Delaney A: the probability that a value of ``x`` exceeds a value of ``y``,
    ties counting half, over every pair (conventions: Vargha-Delaney A; ADR 0401)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    xs, ys = pair[0], np.sort(pair[1])
    left = np.searchsorted(ys, xs, side="left")
    right = np.searchsorted(ys, xs, side="right")
    wins = int(np.sum(left))
    ties = int(np.sum(right - left))
    return float(2 * wins + ties) / float(2 * xs.size * ys.size)


def kolmogorov_smirnov(x: ArrayLike, y: ArrayLike) -> float:
    """The two-sample Kolmogorov-Smirnov statistic: the largest gap between the empirical
    distribution functions of ``x`` and ``y`` (conventions: two-sample Kolmogorov-Smirnov
    statistic; ADR 0402)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(np.sort(a))
    xs, ys = pair
    t = np.unique(np.concatenate([xs, ys]))
    cx = np.searchsorted(xs, t, side="right").astype(np.int64)
    cy = np.searchsorted(ys, t, side="right").astype(np.int64)
    gap = int(np.max(np.abs(cx * ys.size - cy * xs.size)))
    return float(gap) / float(xs.size * ys.size)


def wasserstein_distance(x: ArrayLike, y: ArrayLike) -> float:
    """The first Wasserstein distance between the samples ``x`` and ``y``: the area between
    their empirical distribution functions (conventions: first Wasserstein distance;
    ADR 0403)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(np.sort(a))
    xs, ys = pair
    t = np.unique(np.concatenate([xs, ys]))
    cx = np.searchsorted(xs, t, side="right").astype(np.int64)
    cy = np.searchsorted(ys, t, side="right").astype(np.int64)
    gaps = np.abs(cx * ys.size - cy * xs.size).tolist()
    points = t.tolist()
    total = 0.0
    for m in range(len(points) - 1):
        total += float(gaps[m]) * (points[m + 1] - points[m])
    return total / float(xs.size * ys.size)


def energy_distance(x: ArrayLike, y: ArrayLike) -> float:
    """The energy distance between the samples ``x`` and ``y``: twice the mean absolute
    difference between them less the mean within each, the squared form (conventions: energy
    distance; ADR 0404)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a.tolist())
    xs, ys = pair

    def mean_gap(p: list[float], q: list[float]) -> float:
        total = 0.0
        for u in p:
            for v in q:
                total += abs(u - v)
        return total / (len(p) * len(q))

    e = 2.0 * mean_gap(xs, ys) - mean_gap(xs, xs) - mean_gap(ys, ys)
    return max(e, 0.0)


def cramer_von_mises(x: ArrayLike, y: ArrayLike) -> float:
    """The two-sample Cramer-von Mises statistic: the scaled sum of the squared gaps between
    the empirical distribution functions of ``x`` and ``y`` over the pooled sample
    (conventions: two-sample Cramer-von Mises statistic; ADR 0405)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(np.sort(a))
    xs, ys = pair
    t, copies = np.unique(np.concatenate([xs, ys]), return_counts=True)
    cx = np.searchsorted(xs, t, side="right").astype(np.int64)
    cy = np.searchsorted(ys, t, side="right").astype(np.int64)
    gaps = np.abs(cx * ys.size - cy * xs.size).tolist()
    total = 0.0
    for c, g in zip(copies.tolist(), gaps, strict=True):
        total += float(c) * (float(g) * float(g))
    n = xs.size + ys.size
    return total / (float(xs.size) * float(ys.size) * float(n) * float(n))


def hodges_lehmann(x: ArrayLike, y: ArrayLike) -> float:
    """The Hodges-Lehmann shift estimate: the median of every difference between a value of
    ``x`` and a value of ``y`` (conventions: Hodges-Lehmann shift estimate; ADR 0406)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    d = np.sort((pair[0][:, None] - pair[1][None, :]).ravel())
    m = d.size
    if m % 2 == 1:
        return float(d[m // 2])
    return (float(d[m // 2 - 1]) + float(d[m // 2])) / 2.0


def kl_divergence(p: ArrayLike, q: ArrayLike) -> float:
    """The Kullback-Leibler divergence of the discrete distribution ``p`` from ``q``, each
    normalized by its own sum, in nats (conventions: Kullback-Leibler divergence;
    ADR 0407)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    d = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        if a_ == 0:
            continue
        if b_ == 0:
            raise ValueError("q is zero where p is not: the divergence is infinite")
        pi, qi = a_ / ps, b_ / qs
        d += pi * math.log(pi / qi)
    return max(d, 0.0)


def js_divergence(p: ArrayLike, q: ArrayLike) -> float:
    """The Jensen-Shannon divergence between the discrete distributions ``p`` and ``q``, each
    normalized by its own sum, in nats (conventions: Jensen-Shannon divergence; ADR 0408)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    d = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        pi, qi = a_ / ps, b_ / qs
        mi = (pi + qi) / 2.0
        t = 0.0
        if pi > 0:
            t += pi * math.log(pi / mi)
        if qi > 0:
            t += qi * math.log(qi / mi)
        d += t
    return min(max(d / 2.0, 0.0), math.log(2.0))


def hellinger_distance(p: ArrayLike, q: ArrayLike) -> float:
    """The Hellinger distance between the discrete distributions ``p`` and ``q``, each
    normalized by its own sum, from 0 to 1 (conventions: Hellinger distance; ADR 0409)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    ss = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        d = math.sqrt(a_ / ps) - math.sqrt(b_ / qs)
        ss += d * d
    return min(math.sqrt(ss / 2.0), 1.0)


def bhattacharyya_distance(p: ArrayLike, q: ArrayLike) -> float:
    """The Bhattacharyya distance between the discrete distributions ``p`` and ``q``, each
    normalized by its own sum: minus the log of their overlap (conventions: Bhattacharyya
    distance; ADR 0410)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    bc = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        bc += math.sqrt((a_ / ps) * (b_ / qs))
    if bc == 0:
        raise ValueError("p and q share no support: the distance is infinite")
    return 0.0 - math.log(min(bc, 1.0))


def total_variation_distance(p: ArrayLike, q: ArrayLike) -> float:
    """The total variation distance between the discrete distributions ``p`` and ``q``, each
    normalized by its own sum: half their L1 distance, from 0 to 1 (conventions: total
    variation distance; ADR 0411)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    s = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        s += abs(a_ / ps - b_ / qs)
    return min(s / 2.0, 1.0)


def chi_square_divergence(p: ArrayLike, q: ArrayLike) -> float:
    """The Pearson chi-square divergence of the discrete distribution ``p`` from ``q``, each
    normalized by its own sum (conventions: Pearson chi-square divergence; ADR 0412)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    s = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        if b_ == 0:
            if a_ > 0:
                raise ValueError("q is zero where p is not: the divergence is infinite")
            continue
        qi = b_ / qs
        d = a_ / ps - qi
        s += d * d / qi
    return s


def renyi_divergence(p: ArrayLike, q: ArrayLike, alpha: float) -> float:
    """The order-``alpha`` Rényi divergence of the discrete distribution ``p`` from ``q``,
    each normalized by its own sum (conventions: Rényi divergence; ADR 0413)."""
    al = real(alpha, "alpha")
    if not al > 0 or al == 1:
        raise ValueError("alpha must be above 0 and not 1")
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    s = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        if a_ == 0:
            continue
        if b_ == 0:
            if al > 1:
                raise ValueError("q is zero where p is not: the divergence is infinite")
            continue
        s += math.pow(a_ / ps, al) * math.pow(b_ / qs, 1.0 - al)
    if s == 0:
        raise ValueError("p and q share no support: the divergence is infinite")
    r = math.log(s) / (al - 1.0)
    return r if r > 0 else 0.0


def jeffreys_divergence(p: ArrayLike, q: ArrayLike) -> float:
    """The Jeffreys divergence between the discrete distributions ``p`` and ``q``, each
    normalized by its own sum: the Kullback-Leibler divergence both ways, added
    (conventions: Jeffreys divergence; ADR 0414)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    s = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        if a_ == 0 and b_ == 0:
            continue
        if a_ == 0 or b_ == 0:
            raise ValueError("p and q must be zero at the same indices")
        pi, qi = a_ / ps, b_ / qs
        s += (pi - qi) * math.log(pi / qi)
    return s


def cross_entropy(p: ArrayLike, q: ArrayLike) -> float:
    """The cross-entropy in nats of the discrete distribution ``q`` under ``p``, each
    normalized by its own sum (conventions: cross-entropy; ADR 0415)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    s = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        if a_ == 0:
            continue
        if b_ == 0:
            raise ValueError("q is zero where p is not: the cross-entropy is infinite")
        s += a_ / ps * math.log(b_ / qs)
    return 0.0 - s


def triangular_discrimination(p: ArrayLike, q: ArrayLike) -> float:
    """The triangular discrimination between the discrete distributions ``p`` and ``q``,
    each normalized by its own sum, from 0 to 2 (conventions: triangular discrimination;
    ADR 0416)."""
    pair = []
    for name, v in (("p", p), ("q", q)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        values = a.tolist()
        total = 0.0
        for w in values:
            total += w
        if total <= 0:
            raise ValueError(f"{name} must have a positive sum")
        pair.append((values, total))
    (pv, ps), (qv, qs) = pair
    if len(pv) != len(qv):
        raise ValueError("p and q must have the same length")
    s = 0.0
    for a_, b_ in zip(pv, qv, strict=True):
        if a_ == 0 and b_ == 0:
            continue
        pi, qi = a_ / ps, b_ / qs
        d = pi - qi
        s += d * d / (pi + qi)
    return min(s, 2.0)


def canberra_distance(x: ArrayLike, y: ArrayLike) -> float:
    """The Canberra distance between the real vectors ``x`` and ``y``: each coordinate's
    difference over the sum of their magnitudes, added (conventions: Canberra distance;
    ADR 0417)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a.tolist())
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    s = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ == 0 and b_ == 0:
            continue
        s += abs(a_ - b_) / (abs(a_) + abs(b_))
    return s


def bray_curtis(x: ArrayLike, y: ArrayLike) -> float:
    """The Bray-Curtis dissimilarity between the non-negative vectors ``x`` and ``y``: the
    share of their combined total that does not match (conventions: Bray-Curtis
    dissimilarity; ADR 0418)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and non-negative")
        pair.append(a.tolist())
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    num = 0.0
    den = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        num += abs(a_ - b_)
        den += a_ + b_
    if den <= 0:
        raise ValueError("x and y must not both be all zero")
    return min(num / den, 1.0)


def minkowski_distance(x: ArrayLike, y: ArrayLike, order: float) -> float:
    """The order-``order`` Minkowski distance between the real vectors ``x`` and ``y``,
    scaled by the largest difference so it cannot overflow (conventions: Minkowski distance;
    ADR 0419)."""
    p = real(order, "order")
    if not p >= 1:
        raise ValueError("order must be at least 1")
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a.tolist())
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    diffs = []
    m = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        d = abs(a_ - b_)
        if math.isinf(d):
            raise ValueError("a difference of x and y overflows")
        diffs.append(d)
        if d > m:
            m = d
    if m == 0:
        return 0.0
    s = 0.0
    for d in diffs:
        s += math.pow(d / m, p)
    return m * math.pow(s, 1.0 / p)


def chebyshev_distance(x: ArrayLike, y: ArrayLike) -> float:
    """The Chebyshev distance between the real vectors ``x`` and ``y``: their largest
    coordinate difference (conventions: Chebyshev distance; ADR 0420)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a.tolist())
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    m = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        d = abs(a_ - b_)
        if math.isinf(d):
            raise ValueError("a difference of x and y overflows")
        if d > m:
            m = d
    return m


def hamming_distance(x: ArrayLike, y: ArrayLike) -> int:
    """The Hamming distance between the real vectors ``x`` and ``y``: the number of indices
    where they differ (conventions: Hamming distance; ADR 0421)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{name} must be finite")
        pair.append(a)
    xa, ya = pair
    if xa.size != ya.size:
        raise ValueError("x and y must have the same length")
    return int(np.count_nonzero(xa != ya))


def overlap_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The overlap coefficient of two binary records of 0 and 1: the items both mark 1 over
    the smaller of the two counts of 1, from 0 to 1 (conventions: overlap coefficient;
    ADR 0422)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    smaller = min(int(np.count_nonzero(t)), int(np.count_nonzero(d)))
    if smaller == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return both / smaller


def tversky_index(truth: ArrayLike, decision: ArrayLike, alpha: float, beta: float) -> float:
    """The Tversky index of two binary records of 0 and 1: the items both mark 1 over those
    plus ``alpha`` times the items only ``truth`` marks and ``beta`` times the items only
    ``decision`` marks (conventions: Tversky index; ADR 0423)."""
    al = real(alpha, "alpha")
    be = real(beta, "beta")
    if al < 0:
        raise ValueError("alpha must be at least 0")
    if be < 0:
        raise ValueError("beta must be at least 0")
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = float(np.count_nonzero(t & d))
    fn = float(np.count_nonzero(t & ~d))
    fp = float(np.count_nonzero(~t & d))
    den = (tp + al * fn) + be * fp
    if den == 0:
        raise ValueError("the denominator TP + alpha*FN + beta*FP is zero")
    return tp / den


def simple_matching_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The simple matching coefficient of two binary records of 0 and 1: the items on which
    they agree, 1 or 0, over the length (conventions: simple matching coefficient;
    ADR 0424)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    return int(np.count_nonzero(t == d)) / int(t.size)


def rogers_tanimoto_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Rogers-Tanimoto coefficient of two binary records of 0 and 1: the agreements over
    the agreements plus twice the disagreements (conventions: Rogers-Tanimoto coefficient;
    ADR 0425)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    m = int(np.count_nonzero(t == d))
    u = int(t.size) - m
    return m / (m + 2 * u)


def russell_rao_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Russell-Rao coefficient of two binary records of 0 and 1: the items both mark 1
    over the length (conventions: Russell-Rao coefficient; ADR 0426)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    return int(np.count_nonzero(t & d)) / int(t.size)


def sokal_sneath_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Sokal-Sneath coefficient of two binary records of 0 and 1: the items both mark 1
    over those plus twice the items only one marks 1 (conventions: Sokal-Sneath
    coefficient; ADR 0427)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    den = tp + 2 * int(np.count_nonzero(t ^ d))
    if den == 0:
        raise ValueError("truth or decision must hold at least one 1")
    return tp / den


def kulczynski_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Kulczynski coefficient of two binary records of 0 and 1: the mean of the shares
    of each record's 1s that the other also marks (conventions: Kulczynski coefficient;
    ADR 0428)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return (both / nt + both / nd) / 2


def ochiai_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Ochiai coefficient of two binary records of 0 and 1: the items both mark 1 over
    the geometric mean of the two counts of 1 (conventions: Ochiai coefficient;
    ADR 0429)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return both / math.sqrt(nt * nd)


def yule_q(truth: ArrayLike, decision: ArrayLike) -> float:
    """Yule's Q of two binary records of 0 and 1: ``(TP*TN - FN*FP) / (TP*TN + FN*FP)``,
    their association from -1 to 1 (conventions: Yule's Q; ADR 0430)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    x = tp * tn
    y = fn * fp
    if x + y == 0:
        raise ValueError("TP*TN + FN*FP must not be zero")
    return float(x - y) / float(x + y)


def yule_y(truth: ArrayLike, decision: ArrayLike) -> float:
    """Yule's Y of two binary records of 0 and 1: the coefficient of colligation, from -1
    to 1 (conventions: Yule's Y; ADR 0431)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    x = tp * tn
    y = fn * fp
    if x + y == 0:
        raise ValueError("TP*TN + FN*FP must not be zero")
    sx = math.sqrt(float(x))
    sy = math.sqrt(float(y))
    return (sx - sy) / (sx + sy)


def hamann_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Hamann coefficient of two binary records of 0 and 1: the share of items they
    agree on minus the share they disagree on (conventions: Hamann coefficient; ADR 0432)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    n = int(t.size)
    u = int(np.count_nonzero(t ^ d))
    return (n - 2 * u) / n


def baroni_urbani_buser_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Baroni-Urbani-Buser coefficient of two binary records of 0 and 1: the Jaccard
    index with shared absences let in through ``sqrt(TP*TN)`` (conventions:
    Baroni-Urbani-Buser coefficient; ADR 0433)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    k = tp + fn + fp
    if k == 0:
        raise ValueError("truth or decision must hold at least one 1")
    root = math.sqrt(float(tp * tn))
    return (root + tp) / (root + k)


def sorgenfrei_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Sorgenfrei coefficient of two binary records of 0 and 1: the square of the items
    both mark 1 over the product of the two counts of 1 (conventions: Sorgenfrei
    coefficient; ADR 0434)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return float(both * both) / float(nt * nd)


def forbes_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Forbes coefficient of two binary records of 0 and 1: the items both mark 1 over
    the number expected by chance from the two counts of 1 (conventions: Forbes
    coefficient; ADR 0435)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return float(int(t.size) * both) / float(nt * nd)


def mcconnaughey_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The McConnaughey coefficient of two binary records of 0 and 1: ``(TP**2 - FN*FP)``
    over the product of the two counts of 1, from -1 to 1 (conventions: McConnaughey
    coefficient; ADR 0436)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return float(both * both - (nt - both) * (nd - both)) / float(nt * nd)


def dennis_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Dennis coefficient of two binary records of 0 and 1: the excess of the shared 1s
    over chance in units of its square root (conventions: Dennis coefficient; ADR 0437)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    nt = tp + fn
    nd = tp + fp
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return float(tp * tn - fn * fp) / math.sqrt(float(int(t.size) * nt * nd))


def fager_mcgowan_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Fager-McGowan coefficient of two binary records of 0 and 1: the Ochiai
    coefficient less ``1 / (2 * sqrt(max(|A|, |B|)))`` (conventions: Fager-McGowan
    coefficient; ADR 0438)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold at least one 1")
    return both / math.sqrt(nt * nd) - 1 / (2 * math.sqrt(max(nt, nd)))


def gilbert_skill_score(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Gilbert skill score (equitable threat score) of a binary decision against the
    truth: the threat score with the hits chance expects taken out (conventions: Gilbert
    skill score; ADR 0439)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    chance = (tp + fn) * (tp + fp)
    den = n * (tp + fn + fp) - chance
    if den == 0:
        raise ValueError("truth and decision must not be the same constant record")
    return float(n * tp - chance) / float(den)


def braun_blanquet_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Braun-Blanquet coefficient of two binary records of 0 and 1: the items both mark
    1 over the larger count of 1 (conventions: Braun-Blanquet coefficient; ADR 0440)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    both = int(np.count_nonzero(t & d))
    nt = int(np.count_nonzero(t))
    nd = int(np.count_nonzero(d))
    if nt == 0 and nd == 0:
        raise ValueError("truth and decision must not both be all 0")
    return both / max(nt, nd)


def loevinger_h(truth: ArrayLike, decision: ArrayLike) -> float:
    """Loevinger's H of two binary records of 0 and 1: their covariance over the largest
    the counts of 1 allow, at most 1 (conventions: Loevinger's H; ADR 0441)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt = tp + fn
    nd = tp + fp
    den = n * min(nt, nd) - nt * nd
    if den == 0:
        raise ValueError("truth and decision must not be constant")
    return float(n * tp - nt * nd) / float(den)


def michael_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Michael's coefficient of two binary records of 0 and 1: the cross-product difference
    over the squared agreements and disagreements, from -1 to 1 (conventions: Michael's
    coefficient; ADR 0442)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    den = (tp + tn) ** 2 + (fn + fp) ** 2
    return float(4 * (tp * tn - fn * fp)) / float(den)


def pearson_heron_ii(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Pearson-Heron II coefficient of two binary records of 0 and 1: an approximation
    of the tetrachoric correlation, from -1 to 1 (conventions: Pearson-Heron II coefficient;
    ADR 0443)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    x = tp * tn
    y = fn * fp
    if x + y == 0:
        raise ValueError("TP*TN + FN*FP must not be zero")
    sx = math.sqrt(float(x))
    sy = math.sqrt(float(y))
    return math.cos(math.pi * sy / (sx + sy))


def digby_h(truth: ArrayLike, decision: ArrayLike) -> float:
    """Digby's H of two binary records of 0 and 1: Yule's form at power 3/4, between Yule's
    Y and Yule's Q (conventions: Digby's H; ADR 0444)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    x = tp * tn
    y = fn * fp
    if x + y == 0:
        raise ValueError("TP*TN + FN*FP must not be zero")
    sx = math.sqrt(float(x))
    sy = math.sqrt(float(y))
    px = sx * math.sqrt(sx)
    py = sy * math.sqrt(sy)
    return (px - py) / (px + py)


def cole_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Cole's coefficient of two binary records of 0 and 1: the cross-product difference
    over the extreme the counts of 1 allow on its side, from -1 to 1 (conventions: Cole's
    coefficient; ADR 0445)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt = tp + fn
    nd = tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    cross = n * tp - nt * nd
    if cross >= 0:
        den = n * min(nt, nd) - nt * nd
    else:
        den = nt * nd - n * max(0, nt + nd - n)
    return float(cross) / float(den)


def anderberg_d(truth: ArrayLike, decision: ArrayLike) -> float:
    """Anderberg's D of two binary records of 0 and 1: the gain in predicting each record
    from the other, from 0 to 1/2 (conventions: Anderberg's D; ADR 0446)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    sigma = max(tp, fn) + max(fp, tn) + max(tp, fp) + max(fn, tn)
    base = max(nt, n - nt) + max(nd, n - nd)
    return float(sigma - base) / float(2 * n)


def goodman_kruskal_lambda(truth: ArrayLike, decision: ArrayLike) -> float:
    """Goodman and Kruskal's symmetric lambda of two binary records of 0 and 1: the share of
    prediction errors removed by knowing the other record, from 0 to 1 (conventions: Goodman
    and Kruskal's lambda; ADR 0447)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    sigma = max(tp, fn) + max(fp, tn) + max(tp, fp) + max(fn, tn)
    base = max(nt, n - nt) + max(nd, n - nd)
    if base == 2 * n:
        raise ValueError("truth and decision must not both be constant")
    return float(sigma - base) / float(2 * n - base)


def austin_colwell_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Austin-Colwell coefficient of two binary records of 0 and 1: the arcsine-
    transformed simple matching coefficient, from 0 to 1 (conventions: the Austin-Colwell
    coefficient; ADR 0448)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    p = float(tp + tn) / float(tp + fn + fp + tn)
    return math.asin(math.sqrt(p)) * 2.0 / math.pi


def fossum_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Fossum's coefficient of two binary records of 0 and 1: n (TP - 1/2)^2 over the
    product of the counts of 1, at least 0 (conventions: Fossum's coefficient; ADR 0449)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    nt, nd = tp + fn, tp + fp
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold a 1")
    return float(int(t.size) * (2 * tp - 1) ** 2) / float(4 * nt * nd)


def eyraud_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Eyraud's coefficient of two binary records of 0 and 1: their covariance over the
    product of the four margins (conventions: Eyraud's coefficient; ADR 0450)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    c = float(n * tp - nt * nd)
    return c * float(n * n) / (float(nt * nd) * float((n - nt) * (n - nd)))


def stiles_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Stiles' coefficient of two binary records of 0 and 1: log10 of the continuity-
    corrected chi-square over n (conventions: Stiles' coefficient; ADR 0451)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    e = 2 * abs(n * tp - nt * nd) - n
    if e == 0:
        raise ValueError("|TP TN - FN FP| must not be n/2")
    fe = float(e)
    return math.log10(float(n) * fe * fe / (4.0 * float(nt * nd) * float((n - nt) * (n - nd))))


def mountford_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Mountford's coefficient of two binary records of 0 and 1: twice the shared 1s over
    the products of the counts, at least 0 (conventions: Mountford's coefficient;
    ADR 0452)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    den = tp * fn + tp * fp + 2 * fn * fp
    if den == 0:
        raise ValueError("TP FN + TP FP + 2 FN FP must not be zero")
    return float(2 * tp) / float(den)


def tarwid_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Tarwid's coefficient of two binary records of 0 and 1: the shared 1s against chance
    as a difference over a sum, from -1 to below 1 (conventions: Tarwid's coefficient;
    ADR 0453)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt == 0 or nd == 0:
        raise ValueError("truth and decision must each hold a 1")
    return float(n * tp - nt * nd) / float(n * tp + nt * nd)


def hawkins_dotson_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Hawkins-Dotson coefficient of two binary records of 0 and 1: the mean of the
    Jaccard indices of the 1s and of the 0s, from 0 to 1 (conventions: the Hawkins-Dotson
    coefficient; ADR 0454)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    m = fn + fp
    den = 2 * (tp + m) * (tn + m)
    if den == 0:
        raise ValueError("truth and decision must not both be all 0 or both all 1")
    return float(tp * (tn + m) + tn * (tp + m)) / float(den)


def gower_legendre_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Gower-Legendre coefficient of two binary records of 0 and 1: the matches over
    the matches plus half the mismatches, from 0 to 1 (conventions: the Gower-Legendre
    coefficient; ADR 0455)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    agree = 2 * (tp + tn)
    return float(agree) / float(agree + fn + fp)


def faith_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Faith's coefficient of two binary records of 0 and 1: the shared 1s plus half the
    shared 0s over the length, from 0 to 1 (conventions: Faith's coefficient;
    ADR 0456)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    return float(2 * tp + tn) / float(2 * (tp + fn + fp + tn))


def consonni_todeschini_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Consonni-Todeschini coefficient of two binary records of 0 and 1: the matches on
    a log scale, ln(1 + TP + TN) / ln(1 + n), from 0 to 1 (conventions: the
    Consonni-Todeschini coefficient; ADR 0457)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    return math.log(float(1 + tp + tn)) / math.log(float(1 + tp + fn + fp + tn))


def maxwell_pilliner_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Maxwell-Pilliner coefficient of two binary records of 0 and 1: the cross-product
    difference over the sum of the two records' variances, from -1 to 1 (conventions: the
    Maxwell-Pilliner coefficient; ADR 0458)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    n, nt, nd = tp + fn + fp + tn, tp + fn, tp + fp
    den = nt * (n - nt) + nd * (n - nd)
    if den == 0:
        raise ValueError("truth and decision must not both be constant")
    return float(2 * (tp * tn - fn * fp)) / float(den)


def sokal_sneath_iv(truth: ArrayLike, decision: ArrayLike) -> float:
    """The fourth Sokal-Sneath coefficient of two binary records of 0 and 1: the mean of the
    four conditional probabilities of agreement, from 0 to 1 (conventions: the fourth
    Sokal-Sneath coefficient; ADR 0459)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    tn = n - nt - nd + tp
    return (
        float(tp) / float(nt)
        + float(tp) / float(nd)
        + float(tn) / float(n - nt)
        + float(tn) / float(n - nd)
    ) / 4.0


def sokal_sneath_v(truth: ArrayLike, decision: ArrayLike) -> float:
    """The fifth Sokal-Sneath coefficient of two binary records of 0 and 1: the geometric
    mean of the four conditional probabilities of agreement, from 0 to 1 (conventions: the
    fifth Sokal-Sneath coefficient; ADR 0460)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    tn = n - nt - nd + tp
    return float(tp * tn) / math.sqrt(float(nt * nd) * float((n - nt) * (n - nd)))


def sokal_sneath_iii(truth: ArrayLike, decision: ArrayLike) -> float:
    """The third Sokal-Sneath coefficient of two binary records of 0 and 1: the matches
    per mismatch, at least 0 (conventions: the third Sokal-Sneath coefficient;
    ADR 0461)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if fn + fp == 0:
        raise ValueError("truth and decision must differ somewhere")
    return float(tp + tn) / float(fn + fp)


def kulczynski_i(truth: ArrayLike, decision: ArrayLike) -> float:
    """The first Kulczynski coefficient of two binary records of 0 and 1: the shared 1s
    per mismatch, at least 0 (conventions: the first Kulczynski coefficient;
    ADR 0462)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if fn + fp == 0:
        raise ValueError("truth and decision must differ somewhere")
    return float(tp) / float(fn + fp)


def gilbert_wells_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Gilbert-Wells coefficient of two binary records of 0 and 1: the log of the lift
    of the shared 1s, ln(n·TP / (|A|·|B|)), 0 at independence (conventions: the
    Gilbert-Wells coefficient; ADR 0463)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if tp == 0:
        raise ValueError("truth and decision must share a 1")
    n = int(t.size)
    return math.log(float(n * tp) / float((tp + fn) * (tp + fp)))


def binary_mutual_information(truth: ArrayLike, decision: ArrayLike) -> float:
    """The mutual information of two binary records of 0 and 1: that of their 2x2 table,
    in nats, 0 at independence (conventions: binary mutual information; ADR 0464)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    tn = n - tp - fn - fp
    na, nb = tp + fn, tp + fp
    total = 0.0
    for c, ra, kb in ((tp, na, nb), (fn, na, n - nb), (fp, n - na, nb), (tn, n - na, n - nb)):
        if c > 0:
            total += float(c) / float(n) * math.log(float(n * c) / float(ra * kb))
    return total


def benini_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Benini coefficient of two binary records of 0 and 1: the excess of shared 1s
    over chance as a share of its most, at most 1, 0 at independence (conventions: the
    Benini coefficient; ADR 0465)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    na, nb = tp + fn, tp + fp
    den = n * min(na, nb) - na * nb
    if den == 0:
        raise ValueError("truth and decision must each hold both 0 and 1")
    return float(n * tp - na * nb) / float(den)


def doolittle_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Doolittle coefficient of two binary records of 0 and 1: the square of the phi
    coefficient, from 0 to 1 (conventions: the Doolittle coefficient; ADR 0466)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    na, nb = tp + fn, tp + fp
    u, v = na * nb, (n - na) * (n - nb)
    if u * v == 0:
        raise ValueError("truth and decision must each hold both 0 and 1")
    x = float(n * tp - u)
    return x * x / (float(u) * float(v))


def rogot_goldberg_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Rogot-Goldberg coefficient of two binary records of 0 and 1: the mean of the
    Dice coefficients of the 1s and of the 0s, from 0 to 1 (conventions: the
    Rogot-Goldberg coefficient; ADR 0467)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if 2 * tp + fn + fp == 0 or 2 * tn + fn + fp == 0:
        raise ValueError("truth and decision must not both be all 0 or both all 1")
    return float(tp) / float(2 * tp + fn + fp) + float(tn) / float(2 * tn + fn + fp)


def baroni_urbani_buser_ii(truth: ArrayLike, decision: ArrayLike) -> float:
    """The second Baroni-Urbani-Buser coefficient of two binary records of 0 and 1: the
    first stretched to run from -1 to 1 (conventions: the second Baroni-Urbani-Buser
    coefficient; ADR 0468)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fn + fp == 0:
        raise ValueError("truth and decision must not both be all 0")
    root = math.sqrt(float(tp * tn))
    return (root + float(tp - fn - fp)) / (root + float(tp + fn + fp))


def gower_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """Gower's coefficient of two binary records of 0 and 1: the matches over the
    geometric mean of the margins, at least 0 (conventions: Gower's coefficient;
    ADR 0469)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    tn = n - nt - nd + tp
    return float(tp + tn) / math.sqrt(float(nt * nd) * float((n - nt) * (n - nd)))


def johnson_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Johnson coefficient of two binary records of 0 and 1: the sum of the shares of
    each record's 1s that the other shares, from 0 to 2 (conventions: the Johnson
    coefficient; ADR 0470)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if tp + fn == 0 or tp + fp == 0:
        raise ValueError("truth and decision must each hold a 1")
    return float(tp) / float(tp + fn) + float(tp) / float(tp + fp)


def dispersion_coefficient(truth: ArrayLike, decision: ArrayLike) -> float:
    """The dispersion coefficient of two binary records of 0 and 1: their covariance as
    0/1 values, from -1/4 to 1/4 (conventions: the dispersion coefficient; ADR 0471)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    tn = n - tp - fn - fp
    return float(tp * tn - fn * fp) / float(n * n)


def size_difference(truth: ArrayLike, decision: ArrayLike) -> float:
    """The size difference of two binary records of 0 and 1: the squared share of items
    where they disagree, from 0 to 1 (conventions: the size difference; ADR 0472)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    return float((fn + fp) ** 2) / float(n * n)


def shape_difference(truth: ArrayLike, decision: ArrayLike) -> float:
    """The shape difference of two binary records of 0 and 1: the share of disagreements
    less their squared imbalance, from 0 to 1 (conventions: the shape difference;
    ADR 0473)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    return float(n * (fn + fp) - (fn - fp) ** 2) / float(n * n)


def pattern_difference(truth: ArrayLike, decision: ArrayLike) -> float:
    """The pattern difference of two binary records of 0 and 1: four times the product of
    the shares of the two kinds of disagreement, from 0 to 1 (conventions: the pattern
    difference; ADR 0474)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    return float(4 * fn * fp) / float(n * n)


def variance_dissimilarity(truth: ArrayLike, decision: ArrayLike) -> float:
    """The variance dissimilarity of two binary records of 0 and 1: a quarter of the share
    of items where they disagree, from 0 to 1/4 (conventions: the variance dissimilarity;
    ADR 0475)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    return float(fn + fp) / float(4 * n)


def lance_williams_distance(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Lance-Williams distance of two binary records of 0 and 1: 1 less the Dice
    coefficient, from 0 to 1 (conventions: the Lance-Williams distance; ADR 0476)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if tp + fn + fp == 0:
        raise ValueError("truth and decision must not both be all 0")
    return float(fn + fp) / float(2 * tp + fn + fp)


def chord_distance(truth: ArrayLike, decision: ArrayLike) -> float:
    """The chord distance of two binary records of 0 and 1: sqrt(2 (1 - o)) with o the
    Ochiai coefficient, from 0 to sqrt 2 (conventions: the chord distance of two binary
    records; ADR 0477)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if tp + fn == 0 or tp + fp == 0:
        raise ValueError("truth and decision must each hold a 1")
    o = float(tp) / math.sqrt(float((tp + fn) * (tp + fp)))
    return math.sqrt(2.0 * (1.0 - o))


def binary_chi_square(truth: ArrayLike, decision: ArrayLike) -> float:
    """Pearson's chi-square statistic of the 2x2 table of two binary records of 0 and 1,
    without continuity correction, from 0 to n (conventions: the chi-square statistic of two
    binary records; ADR 0478)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    nt, nd = tp + fn, tp + fp
    if nt in (0, n) or nd in (0, n):
        raise ValueError("truth and decision must not be constant")
    tn = n - nt - nd + tp
    phi = float(tp * tn - fn * fp) / math.sqrt(float(nt * nd) * float((n - nt) * (n - nd)))
    return float(n) * phi * phi


def mcnemar_statistic(truth: ArrayLike, decision: ArrayLike) -> float:
    """McNemar's statistic of two paired binary records of 0 and 1, without continuity
    correction, at least 0 (conventions: McNemar's statistic; ADR 0479)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if fn + fp == 0:
        raise ValueError("truth and decision must not agree everywhere")
    return float((fn - fp) ** 2) / float(fn + fp)


def log_odds_ratio(truth: ArrayLike, decision: ArrayLike) -> float:
    """The log odds ratio of two binary records of 0 and 1: the natural log of the
    diagnostic odds ratio, any real number (conventions: the log odds ratio;
    ADR 0480)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if 0 in (tp, fn, fp, tn):
        raise ValueError("every cell of the table must be nonzero")
    return math.log(float(tp * tn) / float(fn * fp))


def binary_g_statistic(truth: ArrayLike, decision: ArrayLike) -> float:
    """The G statistic of the 2x2 table of two binary records of 0 and 1: 2n times their
    mutual information in nats, at least 0 (conventions: the G statistic of two binary
    records; ADR 0481)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    n = int(t.size)
    tn = n - tp - fn - fp
    na, nb = tp + fn, tp + fp
    total = 0.0
    for c, ra, kb in ((tp, na, nb), (fn, na, n - nb), (fp, n - na, nb), (tn, n - na, n - nb)):
        if c > 0:
            total += float(c) * math.log(float(n * c) / float(ra * kb))
    return 2.0 * total


def positive_likelihood_ratio(truth: ArrayLike, decision: ArrayLike) -> float:
    """The positive likelihood ratio of a binary decision against a binary truth, records of
    0 and 1: the true positive rate over the false positive rate, at least 0 (conventions:
    the positive likelihood ratio; ADR 0482)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fn == 0:
        raise ValueError("truth must hold a 1")
    if fp == 0:
        raise ValueError("the decision must have a false positive")
    return float(tp * (fp + tn)) / float((tp + fn) * fp)


def negative_likelihood_ratio(truth: ArrayLike, decision: ArrayLike) -> float:
    """The negative likelihood ratio of a binary decision against a binary truth, records of
    0 and 1: the false negative rate over the true negative rate, at least 0 (conventions:
    the negative likelihood ratio; ADR 0483)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fn == 0:
        raise ValueError("truth must hold a 1")
    if tn == 0:
        raise ValueError("the decision must have a true negative")
    return float(fn * (fp + tn)) / float((tp + fn) * tn)


def relative_risk(truth: ArrayLike, decision: ArrayLike) -> float:
    """The relative risk of two binary records of 0 and 1, the decision as the exposure: the
    share of truth 1s where the decision is 1 over the share where it is 0, at least 0
    (conventions: the relative risk; ADR 0484)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0:
        raise ValueError("decision must hold a 1")
    if fn == 0:
        raise ValueError("the decision must have a false negative")
    return float(tp * (fn + tn)) / float((tp + fp) * fn)


def attributable_fraction(truth: ArrayLike, decision: ArrayLike) -> float:
    """The attributable fraction among the exposed of two binary records of 0 and 1, the
    decision as the exposure: (RR - 1) / RR with RR the relative risk, at most 1
    (conventions: the attributable fraction; ADR 0485)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp == 0:
        raise ValueError("truth and decision must share a 1")
    if fn + tn == 0:
        raise ValueError("decision must hold a 0")
    return float(tp * (fn + tn) - fn * (tp + fp)) / float(tp * (fn + tn))


def population_attributable_fraction(truth: ArrayLike, decision: ArrayLike) -> float:
    """The population attributable fraction of two binary records of 0 and 1, the decision
    as the exposure: the share of truth 1s that would go if the exposed had the risk of the
    unexposed, at most 1 (conventions: the population attributable fraction; ADR 0486)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fn == 0:
        raise ValueError("truth must hold a 1")
    if fn + tn == 0:
        raise ValueError("decision must hold a 0")
    u = (tp + fn) * (fn + tn)
    return float(u - int(t.size) * fn) / float(u)


def prevalence_threshold(truth: ArrayLike, decision: ArrayLike) -> float:
    """The prevalence threshold of a binary decision against a binary truth, records of 0
    and 1: (sqrt(TPR FPR) - FPR) / (TPR - FPR), from 0 to 1 (conventions: the prevalence
    threshold; ADR 0487)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    a = tp + fn
    b = int(t.size) - a
    if a == 0 or b == 0:
        raise ValueError("truth must hold both 0 and 1")
    den = tp * b - fp * a
    if den == 0:
        raise ValueError("the true and false positive rates must differ")
    return (math.sqrt(float(tp * fp) * float(a * b)) - float(fp * a)) / float(den)


def frequency_bias(truth: ArrayLike, decision: ArrayLike) -> float:
    """The frequency bias of a binary decision against a binary truth, records of 0 and 1:
    the decision's 1s over the truth's, at least 0 (conventions: the frequency bias;
    ADR 0488)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    if tp + fn == 0:
        raise ValueError("truth must hold a 1")
    return float(tp + fp) / float(tp + fn)


def extreme_dependency_score(truth: ArrayLike, decision: ArrayLike) -> float:
    """The extreme dependency score of a binary decision against a binary truth, records of
    0 and 1: 2 ln(|A|/n) / ln(TP/n) - 1, from -1 to 1 (conventions: the extreme dependency
    score; ADR 0489)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    n = float(t.size)
    if tp == 0:
        raise ValueError("truth and decision must share a 1")
    if tp == t.size:
        raise ValueError("truth and decision must not be all 1")
    return 2.0 * math.log(float(tp + fn) / n) / math.log(float(tp) / n) - 1.0


def extremal_dependence_index(truth: ArrayLike, decision: ArrayLike) -> float:
    """The extremal dependence index of a binary decision against a binary truth, records of
    0 and 1: (ln F - ln H) / (ln F + ln H) with H the hit rate and F the false alarm rate,
    from -1 to 1 (conventions: the extremal dependence index; ADR 0490)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    a = tp + fn
    b = int(t.size) - a
    if a == 0 or b == 0:
        raise ValueError("truth must hold both 0 and 1")
    if tp == 0:
        raise ValueError("truth and decision must share a 1")
    if fp == 0:
        raise ValueError("the decision must have a false positive")
    if tp == a and fp == b:
        raise ValueError("decision must hold a 0")
    lf = math.log(float(fp) / float(b))
    lh = math.log(float(tp) / float(a))
    return (lf - lh) / (lf + lh)


def symmetric_extremal_dependence_index(truth: ArrayLike, decision: ArrayLike) -> float:
    """The symmetric extremal dependence index of a binary decision against a binary truth,
    records of 0 and 1, with H the hit rate and F the false alarm rate, from -1 to 1
    (conventions: the symmetric extremal dependence index; ADR 0491)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    a = tp + fn
    b = int(t.size) - a
    tn = b - fp
    if min(tp, fn, fp, tn) == 0:
        raise ValueError("every cell of the table must be non-zero")
    lf = math.log(float(fp) / float(b))
    lg = math.log(float(tn) / float(b))
    lh = math.log(float(tp) / float(a))
    lm = math.log(float(fn) / float(a))
    return (lf - lh - lg + lm) / (lf + lh + lg + lm)


def tetrachoric_approximation(truth: ArrayLike, decision: ArrayLike) -> float:
    """Pearson's cosine approximation to the tetrachoric correlation of two binary records of
    0 and 1: cos(pi / (1 + sqrt(OR))) with OR the odds ratio, from -1 to 1 (conventions: the
    tetrachoric approximation; ADR 0492)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if fn * fp == 0:
        raise ValueError("the records must disagree both ways")
    return math.cos(math.pi / (1.0 + math.sqrt(float(tp * tn) / float(fn * fp))))


def log_odds_ratio_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """Woolf's standard error of the log odds ratio of two binary records of 0 and 1:
    sqrt(1/TP + 1/FN + 1/FP + 1/TN), above 0 (conventions: the standard error of the log
    odds ratio; ADR 0493)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if min(tp, fn, fp, tn) == 0:
        raise ValueError("every cell of the table must be nonzero")
    num = fn * fp * tn + tp * fp * tn + tp * fn * tn + tp * fn * fp
    return math.sqrt(float(num) / float(tp * fn * fp * tn))


def haldane_log_odds_ratio(truth: ArrayLike, decision: ArrayLike) -> float:
    """The log odds ratio of two binary records of 0 and 1 with a half added to every cell
    of the table (Haldane's correction), defined for every table (conventions: the Haldane
    log odds ratio; ADR 0494)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    num = (2 * tp + 1) * (2 * tn + 1)
    return math.log(float(num) / float((2 * fn + 1) * (2 * fp + 1)))


def yule_q_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """The large-sample standard error of Yule's Q of two binary records of 0 and 1:
    (1 - Q^2)/2 times the standard error of the log odds ratio, above 0 (conventions: the
    standard error of Yule's Q; ADR 0495)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if min(tp, fn, fp, tn) == 0:
        raise ValueError("every cell of the table must be nonzero")
    x, y = tp * tn, fn * fp
    num = fn * fp * tn + tp * fp * tn + tp * fn * tn + tp * fn * fp
    w = float(x + y)
    return 2.0 * math.sqrt(float(x * y) * float(num)) / (w * w)


def yule_y_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """The large-sample standard error of Yule's Y of two binary records of 0 and 1:
    (1 - Y^2)/4 times the standard error of the log odds ratio, above 0 (conventions: the
    standard error of Yule's Y; ADR 0496)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if min(tp, fn, fp, tn) == 0:
        raise ValueError("every cell of the table must be nonzero")
    x, y = tp * tn, fn * fp
    num = fn * fp * tn + tp * fp * tn + tp * fn * tn + tp * fn * fp
    w = math.sqrt(float(x)) + math.sqrt(float(y))
    return math.sqrt(float(num)) / (w * w)


def haldane_log_odds_ratio_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """Woolf's standard error of the Haldane log odds ratio of two binary records of 0 and
    1: sqrt of the sum of 1/(cell + 1/2) over the four cells, defined for every table
    (conventions: the standard error of the Haldane log odds ratio; ADR 0497)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    a, b, c, d = 2 * tp + 1, 2 * fn + 1, 2 * fp + 1, 2 * tn + 1
    num = 2 * (b * c * d + a * c * d + a * b * d + a * b * c)
    return math.sqrt(float(num) / float(a * b * c * d))


def log_odds_ratio_wald_z(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Wald z of two binary records of 0 and 1: the log odds ratio over its standard
    error, any real value (conventions: the Wald z of the log odds ratio; ADR 0498)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if min(tp, fn, fp, tn) == 0:
        raise ValueError("every cell of the table must be nonzero")
    x, y = tp * tn, fn * fp
    num = fn * fp * tn + tp * fp * tn + tp * fn * tn + tp * fn * fp
    return math.log(float(x) / float(y)) * math.sqrt(float(x * y) / float(num))


def log_relative_risk_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """The large-sample standard error of the log relative risk of two binary records of 0
    and 1, the decision as the exposure: sqrt(1/TP - 1/(TP + FP) + 1/FN - 1/(FN + TN)), at
    least 0 (conventions: the standard error of the log relative risk; ADR 0499)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp == 0 or fn == 0:
        raise ValueError("TP and FN must be nonzero")
    num = fp * fn * (fn + tn) + tn * tp * (tp + fp)
    return math.sqrt(float(num) / float(tp * (tp + fp) * fn * (fn + tn)))


def log_relative_risk_wald_z(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Wald z of the log relative risk of two binary records of 0 and 1, the decision as
    the exposure: the log relative risk over its standard error, any real value
    (conventions: the Wald z of the log relative risk; ADR 0500)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp == 0 or fn == 0:
        raise ValueError("TP and FN must be nonzero")
    num = fp * fn * (fn + tn) + tn * tp * (tp + fp)
    if num == 0:
        raise ValueError("the standard error must be nonzero")
    p, q = tp * (fn + tn), fn * (tp + fp)
    return math.log(float(p) / float(q)) * math.sqrt(float(p * q) / float(num))


def risk_difference(truth: ArrayLike, decision: ArrayLike) -> float:
    """The risk difference of two binary records of 0 and 1, the decision as the exposure:
    the share of truth 1s where the decision is 1 minus the share where it is 0, from -1 to
    1 (conventions: the risk difference; ADR 0501)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    return float(tp * tn - fn * fp) / float((tp + fp) * (fn + tn))


def risk_difference_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """The large-sample standard error of the risk difference of two binary records of 0 and
    1, the decision as the exposure: sqrt(TP FP/(TP + FP)^3 + FN TN/(FN + TN)^3), at least 0
    (conventions: the standard error of the risk difference; ADR 0502)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    a, b = tp + fp, fn + tn
    return math.sqrt(float(tp * fp) / float(a**3) + float(fn * tn) / float(b**3))


def risk_difference_wald_z(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Wald z of the risk difference of two binary records of 0 and 1, the decision as
    the exposure: the risk difference over its standard error, any real value (conventions:
    the Wald z of the risk difference; ADR 0503)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    a, b = tp + fp, fn + tn
    v = float(tp * fp) / float(a**3) + float(fn * tn) / float(b**3)
    if v == 0:
        raise ValueError("the standard error must be nonzero")
    return float(tp * tn - fn * fp) / float(a * b) / math.sqrt(v)


def number_needed_to_treat(truth: ArrayLike, decision: ArrayLike) -> float:
    """The number needed to treat of two binary records of 0 and 1, the decision as the
    exposure: the reciprocal of the risk difference, of size at least 1 (conventions: the
    number needed to treat; ADR 0504)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    diff = tp * tn - fn * fp
    if diff == 0:
        raise ValueError("the risk difference must be nonzero")
    return float((tp + fp) * (fn + tn)) / float(diff)


def relative_risk_reduction(truth: ArrayLike, decision: ArrayLike) -> float:
    """The relative risk reduction of two binary records of 0 and 1, the decision as the
    exposure: one minus the relative risk, at most 1 (conventions: the relative risk
    reduction; ADR 0505)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0:
        raise ValueError("decision must hold a 1")
    if fn == 0:
        raise ValueError("the decision must have a false negative")
    return float(fn * fp - tp * tn) / float((tp + fp) * fn)


def cohen_h(truth: ArrayLike, decision: ArrayLike) -> float:
    """Cohen's h of two binary records of 0 and 1, the decision as the exposure: the
    difference of 2 asin(sqrt(share)) for the share of truth 1s where the decision is 1 and
    where it is 0, from -pi to pi (conventions: Cohen's h; ADR 0506)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    a = math.atan2(math.sqrt(tp), math.sqrt(fp))
    b = math.atan2(math.sqrt(fn), math.sqrt(tn))
    return 2.0 * (a - b)


def cohen_h_standard_error(truth: ArrayLike, decision: ArrayLike) -> float:
    """The large-sample standard error of Cohen's h of two binary records of 0 and 1, the
    decision as the exposure: sqrt(1/(TP + FP) + 1/(FN + TN)), greater than 0 (conventions:
    the standard error of Cohen's h; ADR 0507)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    return math.sqrt(float(int(t.size)) / float((tp + fp) * (fn + tn)))


def cohen_h_wald_z(truth: ArrayLike, decision: ArrayLike) -> float:
    """The Wald z of Cohen's h of two binary records of 0 and 1, the decision as the
    exposure: Cohen's h over its standard error, any real value (conventions: the Wald z of
    Cohen's h; ADR 0508)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp + fp == 0 or fn + tn == 0:
        raise ValueError("the decision must hold both 0 and 1")
    a = math.atan2(math.sqrt(tp), math.sqrt(fp))
    b = math.atan2(math.sqrt(fn), math.sqrt(tn))
    return 2.0 * (a - b) / math.sqrt(float(int(t.size)) / float((tp + fp) * (fn + tn)))


def log_relative_risk(truth: ArrayLike, decision: ArrayLike) -> float:
    """The natural logarithm of the relative risk of two binary records of 0 and 1, the
    decision as the exposure: ln(TP (FN + TN) / ((TP + FP) FN)), any real value
    (conventions: the log relative risk; ADR 0509)."""
    pair = []
    for name, v in (("truth", truth), ("decision", decision)):
        r = np.asarray(v)
        if r.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(r):
            raise ValueError(f"{name} must be real")
        r = r.astype(np.float64, copy=False)
        if not np.all((r == 0) | (r == 1)):
            raise ValueError(f"{name} must hold only 0 and 1")
        pair.append(r == 1)
    t, d = pair
    if t.size != d.size:
        raise ValueError("truth and decision must be the same length")
    if t.size < 1:
        raise ValueError("truth and decision must not be empty")
    tp = int(np.count_nonzero(t & d))
    fn = int(np.count_nonzero(t & ~d))
    fp = int(np.count_nonzero(~t & d))
    tn = int(t.size) - tp - fn - fp
    if tp == 0 or fn == 0:
        raise ValueError("TP and FN must be nonzero")
    return math.log(float(tp * (fn + tn)) / float(fn * (tp + fp)))


def gini_coefficient(samples: ArrayLike) -> float:
    """The Gini coefficient of a record of values at least 0, not all 0: the mean absolute
    difference over all ordered pairs over twice the mean, from 0 to 1 - 1/n (conventions:
    the Gini coefficient; ADR 0510)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    total = float(np.sum(x))
    if not total > 0:
        raise ValueError("samples must not all be 0")
    k = np.arange(n, dtype=np.float64)
    num = float(np.dot(2 * k - n + 1, np.sort(x)))
    return num / (float(n) * total)


def theil_index(samples: ArrayLike) -> float:
    """The Theil index of a record of values at least 0, not all 0: the mean of
    (x/mean) ln(x/mean), 0 for a value of 0, from 0 to ln n (conventions: the Theil index;
    ADR 0511)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    total = float(np.sum(x))
    if not total > 0:
        raise ValueError("samples must not all be 0")
    r = x / (total / n)
    pos = r[r > 0]
    return float(np.sum(pos * np.log(pos))) / float(n)


def hoover_index(samples: ArrayLike) -> float:
    """The Hoover index of a record of values at least 0, not all 0: the sum of the
    absolute deviations from the mean over twice the total, from 0 to 1 - 1/n (conventions:
    the Hoover index; ADR 0512)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    total = float(np.sum(x))
    if not total > 0:
        raise ValueError("samples must not all be 0")
    dev = float(np.sum(np.abs(x - total / float(n))))
    return dev / (2.0 * total)


def coefficient_of_variation(samples: ArrayLike) -> float:
    """The coefficient of variation of a record with a positive mean: the population
    standard deviation, over n, over the mean (conventions: the coefficient of variation;
    ADR 0513)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    mean = float(np.sum(x)) / float(n)
    if not mean > 0:
        raise ValueError("samples must have a mean greater than 0")
    d = x - mean
    return math.sqrt(float(np.dot(d, d)) / float(n)) / mean


def mean_log_deviation(samples: ArrayLike) -> float:
    """The mean log deviation of a record of positive values: the mean of ln(mean/x), the
    Theil L index, at least 0 (conventions: the mean log deviation; ADR 0514)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if not np.all(x > 0):
        raise ValueError("samples must be greater than 0")
    mean = float(np.sum(x)) / float(n)
    return float(np.sum(np.log(mean / x))) / float(n)


def atkinson_index(samples: ArrayLike, epsilon: float) -> float:
    """The Atkinson index of a record of positive values with inequality aversion
    ``epsilon`` at least 0: one less the power mean of order ``1 - epsilon`` over the mean,
    from 0 to below 1 (conventions: the Atkinson index; ADR 0515)."""
    e = real(epsilon, "epsilon")
    if not e >= 0:
        raise ValueError("epsilon must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if not np.all(x > 0):
        raise ValueError("samples must be greater than 0")
    ratio = x / (float(np.sum(x)) / float(n))
    if e == 1:
        return 1.0 - math.exp(float(np.mean(np.log(ratio))))
    p = 1.0 - e
    return 1.0 - math.pow(float(np.mean(ratio**p)), 1.0 / p)


def generalized_entropy_index(samples: ArrayLike, alpha: float) -> float:
    """The generalized entropy index of order ``alpha`` of a record of positive values: the
    mean log deviation at 0, the Theil index at 1, at least 0 (conventions: the generalized
    entropy index; ADR 0516)."""
    a = real(alpha, "alpha")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if not np.all(x > 0):
        raise ValueError("samples must be greater than 0")
    ratio = x / (float(np.sum(x)) / float(n))
    if a == 0:
        return -float(np.mean(np.log(ratio)))
    if a == 1:
        return float(np.mean(ratio * np.log(ratio)))
    return float(np.mean(ratio**a - 1.0)) / (a * (a - 1.0))


def lorenz_curve(samples: ArrayLike) -> NDArray[np.float64]:
    """The Lorenz curve of a record of values at least 0, not all 0: the ``n + 1`` shares of
    the total held by the smallest ``k`` values, from 0 to exactly 1 (conventions: the
    Lorenz curve; ADR 0517)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = x.shape[0]
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    c = np.cumsum(np.sort(x))
    total = float(c[-1])
    if not total > 0:
        raise ValueError("samples must not all be 0")
    out = np.empty(n + 1, dtype=np.float64)
    out[0] = 0.0
    out[1:] = c / total
    return out


def palma_ratio(samples: ArrayLike) -> float:
    """The Palma ratio of a record of values at least 0: the share of the largest 10% over
    the share of the smallest 40%, from the Lorenz curve joined by straight lines
    (conventions: the Palma ratio; ADR 0518)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    v = np.sort(x)
    c = np.zeros(n + 1, dtype=np.float64)
    c[1:] = np.cumsum(v)
    j4, r4 = divmod(2 * n, 5)
    low = float(c[j4]) + (r4 / 5) * float(v[j4])
    if not low > 0:
        raise ValueError("the smallest 40% of samples must hold some of the total")
    j9, r9 = divmod(9 * n, 10)
    upto = float(c[j9]) + (r9 / 10) * float(v[j9])
    return (float(c[n]) - upto) / low


def quintile_share_ratio(samples: ArrayLike) -> float:
    """The quintile share ratio of a record of values at least 0: the share of the largest
    20% over the share of the smallest 20%, from the Lorenz curve joined by straight lines
    (conventions: the quintile share ratio; ADR 0519)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    v = np.sort(x)
    c = np.zeros(n + 1, dtype=np.float64)
    c[1:] = np.cumsum(v)
    j2, r2 = divmod(n, 5)
    low = float(c[j2]) + (r2 / 5) * float(v[j2])
    if not low > 0:
        raise ValueError("the smallest 20% of samples must hold some of the total")
    j8, r8 = divmod(4 * n, 5)
    upto = float(c[j8]) + (r8 / 5) * float(v[j8])
    return (float(c[n]) - upto) / low


def bonferroni_index(samples: ArrayLike) -> float:
    """The Bonferroni index of a record of at least 2 values at least 0, not all 0: the mean
    over ``k < n`` of the gap between the mean and the mean of the ``k`` smallest, over the
    mean, from 0 to 1 (conventions: the Bonferroni index; ADR 0520)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    c = np.cumsum(np.sort(x))
    total = float(c[-1])
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for k in range(1, n):
        acc += float(c[k - 1]) / k
    return 1.0 - n * acc / ((n - 1) * total)


def zenga_index(samples: ArrayLike) -> float:
    """The Zenga index of a record of at least 2 values at least 0, not all 0: the mean over
    ``k < n`` of the gap between the mean of the ``n - k`` largest and the mean of the ``k``
    smallest, over the former, from 0 to 1 (conventions: the Zenga index; ADR 0521)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    c = np.cumsum(np.sort(x))
    total = float(c[-1])
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for k in range(1, n):
        low = float(c[k - 1])
        acc += (low / k) / ((total - low) / (n - k))
    return 1.0 - acc / (n - 1)


def wolfson_index(samples: ArrayLike) -> float:
    """The Wolfson polarization index of a record of values at least 0 with a median above 0:
    ``2 (mean/median) (1 - 2 L(1/2) - G)``, from the Lorenz curve joined by straight lines
    and the Gini coefficient; at least 0 (conventions: the Wolfson polarization index;
    ADR 0522)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    v = np.sort(x)
    j, rem = divmod(n, 2)
    med = float(v[j]) if rem == 1 else (float(v[j - 1]) + float(v[j])) / 2
    if not med > 0:
        raise ValueError("the median of samples must be above 0")
    total = 0.0
    g = 0.0
    half = 0.0
    for k in range(n):
        if k == j:
            half = total
        a = float(v[k])
        total += a
        g += (2 * k - n + 1) * a
    half += (rem / 2) * float(v[j])
    return 2.0 * (total - 2.0 * half - g / n) / (n * med)


def herfindahl_index(samples: ArrayLike) -> float:
    """The Herfindahl index of a record of values at least 0, not all 0: the sum of the
    squared shares of the total, from 1/n to 1 (conventions: the Herfindahl index;
    ADR 0523)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for a in vals:
        share = a / total
        acc += share * share
    return acc


def concentration_ratio(samples: ArrayLike, k: int) -> float:
    """The concentration ratio of a record of values at least 0, not all 0: the share of the
    total held by the ``k`` largest values, from k/n to 1 (conventions: the concentration
    ratio; ADR 0524)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    kk = count(k, "k")
    if not 1 <= kk <= n:
        raise ValueError("k must be from 1 to the number of samples")
    total = 0.0
    for a in x:
        total += float(a)
    if not total > 0:
        raise ValueError("samples must not all be 0")
    v = np.sort(x)
    top = 0.0
    for i in range(kk):
        top += float(v[n - 1 - i])
    return top / total


def hall_tideman_index(samples: ArrayLike) -> float:
    """The Hall-Tideman index of a record of values at least 0, not all 0: one over twice
    the rank-weighted sum of the shares, ranked from the largest, less 1; from 1/n to 1
    (conventions: the Hall-Tideman index; ADR 0525)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    v = np.sort(x)
    acc = 0.0
    for rank in range(1, n + 1):
        acc += rank * float(v[n - rank])
    return total / (2.0 * acc - total)


def kwoka_dominance_index(samples: ArrayLike) -> float:
    """The Kwoka dominance index of a record of values at least 0, not all 0: the sum of the
    squared gaps between neighbouring shares ranked from the largest, from 0 to 1
    (conventions: the Kwoka dominance index; ADR 0526)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    v = np.sort(x)
    acc = 0.0
    for i in range(n - 1, 0, -1):
        gap = (float(v[i]) - float(v[i - 1])) / total
        acc += gap * gap
    return acc


def hannah_kay_index(samples: ArrayLike, alpha: float) -> float:
    """The Hannah-Kay index of a record of values at least 0, not all 0: the numbers
    equivalent ``(sum s**alpha)**(1/(1 - alpha))`` of the shares, ``exp(-sum s ln s)`` at
    ``alpha = 1``; from 1 to n (conventions: the Hannah-Kay index; ADR 0527)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    a = real(alpha, "alpha")
    if not a > 0:
        raise ValueError("alpha must be above 0")
    acc = 0.0
    if a == 1:
        for value in vals:
            share = value / total
            if share > 0:
                acc += share * math.log(share)
        return math.exp(-acc)
    for value in vals:
        acc += math.pow(value / total, a)
    return math.pow(acc, 1.0 / (1.0 - a))


def pielou_evenness(samples: ArrayLike) -> float:
    """Pielou's evenness of a record of at least 2 values at least 0, not all 0: the Shannon
    entropy of the shares over ``ln n``, from 0 to 1 (conventions: Pielou's evenness;
    ADR 0528)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for value in vals:
        share = value / total
        if share > 0:
            acc += share * math.log(share)
    return -acc / math.log(n)


def simpson_diversity(samples: ArrayLike) -> float:
    """The Gini-Simpson index of a record of values at least 0, not all 0: one less the sum
    of the squared shares, from 0 to 1 - 1/n (conventions: the Gini-Simpson index;
    ADR 0529)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for value in vals:
        share = value / total
        acc += share * share
    return 1.0 - acc


def berger_parker_index(samples: ArrayLike) -> float:
    """The Berger-Parker index of a record of values at least 0, not all 0: the largest
    share of the total, from 1/n to 1 (conventions: the Berger-Parker index; ADR 0530)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    return max(vals) / total


def heip_evenness(samples: ArrayLike) -> float:
    """Heip's evenness of a record of at least 2 values at least 0, not all 0: the
    exponential of the Shannon entropy of the shares, less 1, over ``n - 1``; from 0 to 1
    (conventions: Heip's evenness; ADR 0531)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for value in vals:
        share = value / total
        if share > 0:
            acc += share * math.log(share)
    return (math.exp(-acc) - 1.0) / (n - 1)


def simpson_evenness(samples: ArrayLike) -> float:
    """Simpson's evenness of a record of values at least 0, not all 0: one over n times the
    sum of the squared shares, from 1/n to 1 (conventions: Simpson's evenness; ADR 0532)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for value in vals:
        share = value / total
        acc += share * share
    return 1.0 / (n * acc)


def camargo_evenness(samples: ArrayLike) -> float:
    """Camargo's evenness of a record of values at least 0, not all 0: one less the sum of
    the gaps between every pair of shares over n, from 1/n to 1 (conventions: Camargo's
    evenness; ADR 0533)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    shares = [value / total for value in vals]
    acc = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            acc += abs(shares[i] - shares[j])
    return 1.0 - acc / n


def smith_wilson_evenness(samples: ArrayLike) -> float:
    """The Smith-Wilson evenness of a record of values above 0: one less 2/pi times the
    arctangent of the variance of the logarithms, from 0 to 1 (conventions: the
    Smith-Wilson evenness; ADR 0534)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x <= 0):
        raise ValueError("samples must be above 0")
    logs = [math.log(float(a)) for a in x]
    mean = 0.0
    for value in logs:
        mean += value
    mean /= n
    acc = 0.0
    for value in logs:
        d = value - mean
        acc += d * d
    return 1.0 - 2.0 / math.pi * math.atan(acc / n)


def bulla_evenness(samples: ArrayLike) -> float:
    """Bulla's evenness of a record of at least 2 values at least 0, not all 0: the overlap
    of the shares with equal shares, rescaled from 0 to 1 (conventions: Bulla's evenness;
    ADR 0535)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    even = 1.0 / n
    acc = 0.0
    for value in vals:
        acc += min(value / total, even)
    return (acc - even) / (1.0 - even)


def hill_ratio_evenness(samples: ArrayLike) -> float:
    """The Hill ratio evenness of a record of values at least 0, not all 0: the Hill number
    of order 2 over that of order 1, above 0 and at most 1 (conventions: the Hill ratio
    evenness; ADR 0536)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    sq = 0.0
    ent = 0.0
    for value in vals:
        share = value / total
        sq += share * share
        if share > 0:
            ent += share * math.log(share)
    return 1.0 / sq / math.exp(-ent)


def alatalo_evenness(samples: ArrayLike) -> float:
    """Alatalo's evenness of a record of values at least 0 with at least 2 above 0: the Hill
    number of order 2 less 1 over that of order 1 less 1, above 0 and at most 1
    (conventions: Alatalo's evenness; ADR 0537)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    sq = 0.0
    ent = 0.0
    positive = 0
    for value in vals:
        share = value / total
        sq += share * share
        if share > 0:
            ent += share * math.log(share)
            positive += 1
    if positive < 2:
        raise ValueError("samples must have at least 2 values above 0")
    return (1.0 / sq - 1.0) / (math.exp(-ent) - 1.0)


def sheldon_evenness(samples: ArrayLike) -> float:
    """Sheldon's evenness of a record of values at least 0, not all 0: the exponential of
    the Shannon entropy of the shares over n, from 1/n to 1 (conventions: Sheldon's
    evenness; ADR 0538)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    acc = 0.0
    for value in vals:
        share = value / total
        if share > 0:
            acc += share * math.log(share)
    return math.exp(-acc) / n


def mcintosh_dominance(samples: ArrayLike) -> float:
    """The McIntosh dominance of a record of values at least 0 totalling more than 1: the
    total less the Euclidean length over the total less its square root; 0 when one value
    holds the total (conventions: the McIntosh dominance; ADR 0539)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 1:
        raise ValueError("samples must total more than 1")
    sq = 0.0
    for value in vals:
        sq += value * value
    return (total - math.sqrt(sq)) / (total - math.sqrt(total))


def mcintosh_evenness(samples: ArrayLike) -> float:
    """The McIntosh evenness of a record of at least 2 values at least 0, not all 0: the
    total less the Euclidean length over the total less the total over the square root of
    n; from 0 to 1 (conventions: the McIntosh evenness; ADR 0540)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 2:
        raise ValueError("samples must have at least 2 values")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    sq = 0.0
    for value in vals:
        sq += value * value
    return (total - math.sqrt(sq)) / (total - total / math.sqrt(n))


def menhinick_index(samples: ArrayLike) -> float:
    """Menhinick's index of a record of values at least 0, not all 0: the count of values
    above 0 over the square root of the total (conventions: Menhinick's index; ADR 0541)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    k = 0
    for value in vals:
        if value > 0:
            k += 1
    return k / math.sqrt(total)


def margalef_index(samples: ArrayLike) -> float:
    """Margalef's index of a record of values at least 0 totalling more than 1: one less
    than the count of values above 0 over the logarithm of the total (conventions:
    Margalef's index; ADR 0542)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 1:
        raise ValueError("samples must total more than 1")
    k = 0
    for value in vals:
        if value > 0:
            k += 1
    return (k - 1) / math.log(total)


def gleason_index(samples: ArrayLike) -> float:
    """Gleason's index of a record of values at least 0 totalling more than 1: the count of
    values above 0 over the logarithm of the total (conventions: Gleason's index;
    ADR 0543)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 1:
        raise ValueError("samples must total more than 1")
    k = 0
    for value in vals:
        if value > 0:
            k += 1
    return k / math.log(total)


def goods_coverage(samples: ArrayLike) -> float:
    """Good's coverage of a record of values at least 0, not all 0: one less the count of
    values equal to 1 over the total (conventions: Good's coverage; ADR 0544)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    ones = 0
    for value in vals:
        if value == 1:
            ones += 1
    return 1.0 - ones / total


def chao1_richness(samples: ArrayLike) -> float:
    """The bias-corrected Chao1 richness of a record of values at least 0, not all 0: the
    count of values above 0 plus a term in the counts of values equal to 1 and to 2
    (conventions: the Chao1 richness; ADR 0545)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    k = 0
    ones = 0
    twos = 0
    for value in vals:
        if value > 0:
            k += 1
        if value == 1:
            ones += 1
        elif value == 2:
            twos += 1
    return k + ones * (ones - 1) / (2.0 * (twos + 1))


def brillouin_index(samples: ArrayLike) -> float:
    """The Brillouin index of a record of whole numbers at least 0, not all 0, in nats: the
    logarithm of the multinomial coefficient of the counts over their total (conventions:
    the Brillouin index; ADR 0546)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    parts = 0.0
    for value in vals:
        for j in range(2, int(value) + 1):
            parts += math.log(j)
    whole = 0.0
    for j in range(2, int(total) + 1):
        whole += math.log(j)
    return (whole - parts) / total


def brillouin_evenness(samples: ArrayLike) -> float:
    """The Brillouin evenness of a record of whole numbers at least 0, at least 2 above 0:
    the Brillouin index over its largest value for the same total and count of kinds
    (conventions: the Brillouin evenness; ADR 0547)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    k = 0
    parts = 0.0
    for value in vals:
        if value > 0:
            k += 1
        for j in range(2, int(value) + 1):
            parts += math.log(j)
    if k < 2:
        raise ValueError("samples must have at least 2 values above 0")
    whole = 0.0
    for j in range(2, int(total) + 1):
        whole += math.log(j)
    c, rem = divmod(int(total), k)
    low = 0.0
    for j in range(2, c + 1):
        low += math.log(j)
    high = low + math.log(c + 1)
    return (whole - parts) / (whole - (k - rem) * low - rem * high)


def hurlbert_pie(samples: ArrayLike) -> float:
    """Hurlbert's PIE of a record of values at least 0 totalling more than 1: the
    Gini-Simpson index times N/(N - 1), the chance that two individuals drawn without
    replacement differ in kind (conventions: Hurlbert's PIE; ADR 0548)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 1:
        raise ValueError("samples must total more than 1")
    acc = 0.0
    for value in vals:
        share = value / total
        acc += share * share
    return total / (total - 1.0) * (1.0 - acc)


def strong_dominance(samples: ArrayLike) -> float:
    """Strong's dominance of a record of values at least 0, not all 0: the largest gap
    between the share held by the i largest values and i over the count of values above 0
    (conventions: Strong's dominance; ADR 0549)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    desc = sorted((value for value in vals if value > 0), reverse=True)
    k = len(desc)
    best = 0.0
    run = 0.0
    for i, value in enumerate(desc, start=1):
        run += value
        best = max(best, run / total - i / k)
    return best


def fisher_alpha(samples: ArrayLike) -> float:
    """Fisher's alpha of a record of whole numbers at least 0 totalling more than the count
    of values above 0: the log-series alpha with k = alpha ln(1 + N/alpha)
    (conventions: Fisher's alpha; ADR 0550)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    k = 0
    for value in vals:
        if value > 0:
            k += 1
    if not k < total:
        raise ValueError("samples must total more than the count of values above 0")

    def count(alpha: float) -> float:
        x = total / alpha
        u = 1.0 + x
        lp = x if u == 1.0 else math.log(u) * x / (u - 1.0)
        return alpha * lp

    lo = 1.0
    while count(lo) >= k:
        lo /= 2.0
    hi = 1.0
    while count(hi) <= k:
        hi *= 2.0
    for _ in range(100):
        mid = math.sqrt(lo) * math.sqrt(hi)
        if count(mid) < k:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo) * math.sqrt(hi)


def ace_richness(samples: ArrayLike) -> float:
    """The ACE richness of a record of whole numbers at least 0: Chao and Lee's
    abundance-based coverage estimator, kinds with counts 1 to 10 as the rare group
    (conventions: the ACE richness; ADR 0551)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    s_abund = 0
    s_rare = 0
    ones = 0
    n_rare = 0.0
    pairs = 0.0
    for value in vals:
        if value > 10:
            s_abund += 1
        elif value > 0:
            s_rare += 1
            n_rare += value
            pairs += value * (value - 1.0)
            if value == 1:
                ones += 1
    if s_rare == 0:
        return float(s_abund)
    if ones == s_rare:
        raise ValueError("samples must have a rare value above 1")
    cover = 1.0 - ones / n_rare
    gamma = max(s_rare / cover * pairs / (n_rare * (n_rare - 1.0)) - 1.0, 0.0)
    return s_abund + s_rare / cover + ones / cover * gamma


def rarefied_richness(samples: ArrayLike, size: int) -> float:
    """The rarefied richness of a record of whole numbers at least 0: the expected count of
    kinds among ``size`` individuals drawn from them without replacement
    (conventions: the rarefied richness; ADR 0552)."""
    draws = count(size, "size")
    if draws < 1:
        raise ValueError("size must be at least 1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    if draws > total:
        raise ValueError("size must be at most the total")
    acc = 0.0
    for value in vals:
        if value > 0:
            miss = 1.0
            for j in range(int(value)):
                miss *= (total - draws - j) / (total - j)
                if miss == 0:
                    break
            acc += 1.0 - miss
    return acc


def chao_jost_coverage(samples: ArrayLike) -> float:
    """The Chao-Jost coverage of a record of whole numbers at least 0 totalling more than 1:
    Good's coverage corrected with the counts of values equal to 1 and to 2
    (conventions: the Chao-Jost coverage; ADR 0553)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    if not total > 1:
        raise ValueError("samples must total more than 1")
    ones = 0
    twos = 0
    for value in vals:
        if value == 1:
            ones += 1
        elif value == 2:
            twos += 1
    if ones == 0:
        return 1.0
    a = (total - 1.0) * ones
    return 1.0 - ones / total * (a / (a + 2.0 * twos))


def chao_shen_entropy(samples: ArrayLike) -> float:
    """The Chao-Shen entropy of a record of whole numbers at least 0, not all 0, in nats:
    the coverage-adjusted Horvitz-Thompson estimate of the Shannon entropy
    (conventions: the Chao-Shen entropy; ADR 0554)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    ones = 0
    for value in vals:
        if value == 1:
            ones += 1
    if ones == total:
        ones -= 1
    cover = 1.0 - ones / total
    acc = 0.0
    for value in vals:
        if value > 0:
            share = cover * (value / total)
            acc -= share * math.log(share) / (1.0 - (1.0 - share) ** total)
    return acc


def miller_madow_entropy(samples: ArrayLike) -> float:
    """The Miller-Madow entropy of a record of whole numbers at least 0, not all 0, in nats:
    the plug-in Shannon entropy plus (k - 1)/(2N)
    (conventions: the Miller-Madow entropy; ADR 0555)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    k = 0
    acc = 0.0
    for value in vals:
        if value > 0:
            k += 1
            share = value / total
            acc -= share * math.log(share)
    return acc + (k - 1) / (2.0 * total)


def hutcheson_variance(samples: ArrayLike) -> float:
    """Hutcheson's variance of a record of whole numbers at least 0, not all 0, in nats
    squared: the large-sample variance of its plug-in Shannon entropy
    (conventions: Hutcheson's variance; ADR 0556)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    k = 0
    lin = 0.0
    sq = 0.0
    for value in vals:
        if value > 0:
            k += 1
            share = value / total
            log = math.log(share)
            lin += share * log
            sq += share * log * log
    return (sq - lin * lin) / total + (k - 1) / (2.0 * total * total)


def _hutcheson_parts(samples: ArrayLike, name: str) -> tuple[float, float]:
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError(f"{name} must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be finite")
    if int(x.shape[0]) < 1:
        raise ValueError(f"{name} must not be empty")
    if np.any(x < 0):
        raise ValueError(f"{name} must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError(f"{name} must be whole numbers")
    vals = [float(v) for v in x]
    total = 0.0
    for v in vals:
        total += v
    if not total > 0:
        raise ValueError(f"{name} must not all be 0")
    if total > 10_000_000:
        raise ValueError(f"{name} must total at most 10 000 000")
    k = 0
    lin = 0.0
    sq = 0.0
    for value in vals:
        if value > 0:
            k += 1
            share = value / total
            log = math.log(share)
            lin += share * log
            sq += share * log * log
    return -lin, (sq - lin * lin) / total + (k - 1) / (2.0 * total * total)


def hutcheson_t(a: ArrayLike, b: ArrayLike) -> float:
    """Hutcheson's t between two records of whole numbers at least 0, not all 0: the
    difference of their plug-in Shannon entropies over the root of the summed Hutcheson
    variances (conventions: Hutcheson's t; ADR 0557)."""
    h_a, v_a = _hutcheson_parts(a, "a")
    h_b, v_b = _hutcheson_parts(b, "b")
    spread = v_a + v_b
    if not spread > 0:
        raise ValueError("a and b must not both have a single kind")
    return (h_a - h_b) / math.sqrt(spread)


def jackknife_entropy(samples: ArrayLike) -> float:
    """The jackknife Shannon entropy of a record of whole numbers at least 0 totalling more
    than 1, in nats: Zahl's jackknife over individuals of the plug-in entropy
    (conventions: the jackknife Shannon entropy; ADR 0558)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    if not total > 1:
        raise ValueError("samples must total more than 1")
    s_log = 0.0
    for value in vals:
        if value > 0:
            s_log += value * math.log(value)
    rest = total - 1.0
    acc = 0.0
    for value in vals:
        if value > 0:
            less = value - 1.0
            drop = s_log - value * math.log(value)
            if less > 0:
                drop += less * math.log(less)
            acc += value * (math.log(rest) - drop / rest)
    return total * (math.log(total) - s_log / total) - rest / total * acc


def grassberger_entropy(samples: ArrayLike) -> float:
    """The Grassberger entropy of a record of whole numbers at least 0, not all 0, in nats:
    Grassberger's 2003 digamma-based estimate of the Shannon entropy
    (conventions: the Grassberger entropy; ADR 0559)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    acc = 0.0
    for value in vals:
        if value > 0:
            odd = 0.0
            for j in range(int(value) // 2):
                odd += 2.0 / (2 * j + 1)
            acc += value * odd
    return math.log(total) + 0.5772156649015329 + math.log(2.0) - acc / total


def bonachela_entropy(samples: ArrayLike) -> float:
    """The Bonachela entropy of a record of whole numbers at least 0, not all 0, in nats:
    the balanced small-sample estimate of Bonachela, Hinrichsen and Munoz
    (conventions: the Bonachela entropy; ADR 0560)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000_000:
        raise ValueError("samples must total at most 10 000 000")
    need = {int(value) + 1 for value in vals if value > 0}
    marks: dict[int, float] = {}
    harm = 0.0
    for j in range(1, int(total) + 3):
        harm += 1.0 / j
        if j in need:
            marks[j] = harm
    acc = 0.0
    for value in vals:
        if value > 0:
            acc += (value + 1.0) * (harm - marks[int(value) + 1])
    return acc / (total + 2.0)


def zhang_entropy(samples: ArrayLike) -> float:
    """Zhang's entropy of a record of whole numbers at least 0 totalling more than 1 and at
    most 10 000, in nats: Zhang's 2012 estimate of the Shannon entropy
    (conventions: Zhang's entropy; ADR 0561)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000:
        raise ValueError("samples must total at most 10 000")
    if not total > 1:
        raise ValueError("samples must total more than 1")
    inner: dict[float, float] = {}
    acc = 0.0
    for value in vals:
        if value > 0:
            if value not in inner:
                prod = 1.0
                part = 0.0
                for step in range(1, int(total - value) + 1):
                    prod *= 1.0 - (value - 1.0) / (total - step)
                    part += prod / step
                inner[value] = part
            acc += value / total * inner[value]
    return acc


def chao_wang_jost_entropy(samples: ArrayLike) -> float:
    """The Chao-Wang-Jost entropy of a record of whole numbers at least 0 totalling more
    than 1 and at most 10 000, in nats: the seen kinds through Zhang's series and the unseen
    through the singletons and doubletons (conventions: the Chao-Wang-Jost entropy;
    ADR 0562)."""
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    if np.any(x != np.floor(x)):
        raise ValueError("samples must be whole numbers")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    if total > 10_000:
        raise ValueError("samples must total at most 10 000")
    if not total > 1:
        raise ValueError("samples must total more than 1")
    ones = 0
    twos = 0
    need: set[int] = set()
    for value in vals:
        if value == 1:
            ones += 1
        elif value == 2:
            twos += 1
        if 0 < value < total:
            need.add(int(value) - 1)
    marks: dict[int, float] = {0: 0.0}
    harm = 0.0
    for j in range(1, int(total)):
        harm += 1.0 / j
        if j in need:
            marks[j] = harm
    acc = 0.0
    for value in vals:
        if 0 < value < total:
            acc += value / total * (harm - marks[int(value) - 1])
    if ones == 0:
        return acc
    if twos > 0:
        a = 2.0 * twos / ((total - 1.0) * ones + 2.0 * twos)
    else:
        a = 2.0 / ((total - 1.0) * (ones - 1) + 2.0)
    q = 1.0 - a
    w = 1.0
    part = 0.0
    if a * total >= 1.0:
        m = 0
        while True:
            term = w / (total + m)
            if part + term == part:
                break
            part += term
            w *= q
            m += 1
        rest = q * part
    else:
        for step in range(1, int(total)):
            w *= q
            part += w / step
        rest = q ** (1.0 - total) * (-math.log(a) - part)
    return acc + ones / total * rest


def hill_number(samples: ArrayLike, order: float) -> float:
    """The Hill number of order ``order`` of a record of values at least 0, not all 0: the
    effective number of kinds, ``(sum p**q)**(1/(1-q))`` over the shares above 0
    (conventions: the Hill number; ADR 0563)."""
    q = real(order, "order")
    if not q >= 0:
        raise ValueError("order must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    shares = [a / total for a in vals if a > 0]
    if q == 0:
        return float(len(shares))
    if q == 1:
        acc = 0.0
        for p in shares:
            acc += p * math.log(p)
        return math.exp(-acc)
    if abs(q - 1.0) < 0.5:
        s = 0.0
        for p in shares:
            s += p * math.expm1((q - 1.0) * math.log(p))
        return math.exp(math.log1p(s) / (1.0 - q))
    m = max(shares)
    t = 0.0
    for p in shares:
        t += (p / m) ** q
    return math.exp((q * math.log(m) + math.log(t)) / (1.0 - q))


def hill_evenness(samples: ArrayLike, order: float) -> float:
    """Hill evenness of order ``order`` of a record of values at least 0, not all 0: the
    Hill number over the count of values above 0, from 1/K to 1 (conventions: Hill
    evenness; ADR 0564)."""
    d = hill_number(samples, order)
    k = int(np.count_nonzero(np.asarray(samples, dtype=np.float64) > 0))
    return d / k


def patil_taillie_diversity(samples: ArrayLike, beta: float) -> float:
    """The Patil-Taillie diversity of order ``beta`` of a record of values at least 0, not
    all 0: ``(1 - sum p**(beta+1))/beta`` over the shares above 0, the Shannon entropy at
    ``beta = 0`` (conventions: the Patil-Taillie diversity; ADR 0565)."""
    b = real(beta, "beta")
    if not b >= -1:
        raise ValueError("beta must be at least -1")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    shares = [a / total for a in vals if a > 0]
    acc = 0.0
    if b == 0:
        for p in shares:
            acc += p * math.log(p)
        return -acc
    for p in shares:
        acc += p * math.expm1(b * math.log(p))
    return -acc / b


def renyi_diversity(samples: ArrayLike, order: float) -> float:
    """The Renyi diversity of order ``order`` of a record of values at least 0, not all 0,
    in nats: ``ln(sum p**q)/(1-q)`` over the shares above 0, the log of the Hill number
    (conventions: the Renyi diversity of counts; ADR 0566)."""
    q = real(order, "order")
    if not q >= 0:
        raise ValueError("order must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    shares = [a / total for a in vals if a > 0]
    if q == 0:
        return math.log(len(shares))
    if q == 1:
        acc = 0.0
        for p in shares:
            acc += p * math.log(p)
        return -acc
    if abs(q - 1.0) < 0.5:
        s = 0.0
        for p in shares:
            s += p * math.expm1((q - 1.0) * math.log(p))
        return math.log1p(s) / (1.0 - q)
    m = max(shares)
    t = 0.0
    for p in shares:
        t += (p / m) ** q
    return (q * math.log(m) + math.log(t)) / (1.0 - q)


def renyi_evenness(samples: ArrayLike, order: float) -> float:
    """Renyi evenness of order ``order`` of a record of values at least 0, at least two
    of them above 0: the Renyi diversity of counts over ln K, from 0 to 1 (conventions:
    Renyi evenness; ADR 0567)."""
    h = renyi_diversity(samples, order)
    k = int(np.count_nonzero(np.asarray(samples, dtype=np.float64) > 0))
    if k < 2:
        raise ValueError("samples must have at least two values above 0")
    return h / math.log(k)


def tsallis_diversity(samples: ArrayLike, order: float) -> float:
    """The Tsallis diversity of order ``order`` of a record of values at least 0, not all
    0: ``(1 - sum p**q)/(q - 1)`` over the shares above 0, the Shannon entropy at ``q = 1``
    (conventions: the Tsallis diversity of counts; ADR 0568)."""
    q = real(order, "order")
    if not q >= 0:
        raise ValueError("order must be at least 0")
    x = np.asarray(samples)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if np.iscomplexobj(x):
        raise ValueError("samples must be real")
    x = x.astype(np.float64, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite")
    n = int(x.shape[0])
    if n < 1:
        raise ValueError("samples must not be empty")
    if np.any(x < 0):
        raise ValueError("samples must be at least 0")
    vals = [float(a) for a in x]
    total = 0.0
    for a in vals:
        total += a
    if not total > 0:
        raise ValueError("samples must not all be 0")
    shares = [a / total for a in vals if a > 0]
    acc = 0.0
    if q == 1:
        for p in shares:
            acc += p * math.log(p)
        return -acc
    b = q - 1.0
    for p in shares:
        acc += p * math.expm1(b * math.log(p))
    return -acc / b


def tsallis_evenness(samples: ArrayLike, order: float) -> float:
    """Tsallis evenness of order ``order`` of a record of values at least 0, at least two
    of them above 0: the Tsallis diversity of counts over its value for K equal shares,
    from 0 to 1 (conventions: Tsallis evenness; ADR 0569)."""
    d = tsallis_diversity(samples, order)
    k = int(np.count_nonzero(np.asarray(samples, dtype=np.float64) > 0))
    if k < 2:
        raise ValueError("samples must have at least two values above 0")
    q = float(order)
    if q == 1:
        return d / math.log(k)
    return d / (-math.expm1((1.0 - q) * math.log(k)) / (q - 1.0))


def sharma_mittal_diversity(samples: ArrayLike, order: float, degree: float) -> float:
    """The Sharma-Mittal diversity of order ``order`` and degree ``degree`` of a record of
    values at least 0, not all 0: the Renyi diversity at degree 1, the Tsallis diversity at
    degree equal to order (conventions: the Sharma-Mittal diversity of counts; ADR 0570)."""
    r = real(degree, "degree")
    h = renyi_diversity(samples, order)
    if r == 1:
        return h
    return math.expm1((1.0 - r) * h) / (1.0 - r)


def pianka_overlap(x: ArrayLike, y: ArrayLike) -> float:
    """Pianka's niche overlap of the records ``x`` and ``y`` of values at least 0, each with a
    value above 0: sum(p*q)/sqrt(sum(p**2)*sum(q**2)) on their shares, from 0 to 1
    (conventions: Pianka's niche overlap; ADR 0571)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) / top for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    sxy = 0.0
    sxx = 0.0
    syy = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        sxy += a_ * b_
        sxx += a_ * a_
        syy += b_ * b_
    return min(sxy / math.sqrt(sxx * syy), 1.0)


def czekanowski_similarity(x: ArrayLike, y: ArrayLike) -> float:
    """The proportional similarity of the records ``x`` and ``y`` of values at least 0, each
    with a value above 0: sum(min(p, q)) over their shares, from 0 to 1 (conventions:
    proportional similarity; ADR 0572)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        scaled = [float(b) / top for b in a]
        total = 0.0
        for b in scaled:
            total += b
        pair.append([b / total for b in scaled])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    acc = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        acc += min(a_, b_)
    return min(acc, 1.0)


def morisita_horn_overlap(x: ArrayLike, y: ArrayLike) -> float:
    """The Morisita-Horn overlap of the records ``x`` and ``y`` of values at least 0, each with
    a value above 0: 2*sum(p*q)/(sum(p**2) + sum(q**2)) on their shares, from 0 to 1
    (conventions: Morisita-Horn overlap; ADR 0573)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        scaled = [float(b) / top for b in a]
        total = 0.0
        for b in scaled:
            total += b
        pair.append([b / total for b in scaled])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    sxy = 0.0
    sxx = 0.0
    syy = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        sxy += a_ * b_
        sxx += a_ * a_
        syy += b_ * b_
    return min(2.0 * sxy / (sxx + syy), 1.0)


def horn_overlap(x: ArrayLike, y: ArrayLike) -> float:
    """Horn's information overlap of the records ``x`` and ``y`` of values at least 0, each
    with a value above 0: the information shared by the two records over its largest value
    for their totals, from 0 to 1 (conventions: Horn's information overlap; ADR 0574)."""
    pair = []
    tops = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        tops.append(top)
        pair.append([float(b) for b in a])
    if len(pair[0]) != len(pair[1]):
        raise ValueError("x and y must have the same length")
    m = max(tops)
    xv = [a_ / m for a_ in pair[0]]
    yv = [b_ / m for b_ in pair[1]]

    def term(a_: float, b_: float) -> float:
        if a_ == 0 or b_ == 0:
            return 0.0
        return a_ * math.log1p(b_ / a_) + b_ * math.log1p(a_ / b_)

    num = 0.0
    tx = 0.0
    ty = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        num += term(a_, b_)
        tx += a_
        ty += b_
    return min(num / term(tx, ty), 1.0)


def whittaker_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Whittaker's beta diversity of the records ``x`` and ``y`` of values at least 0, each
    with a value above 0: 2*S_union/(S_x + S_y) - 1 on the kinds above 0, from 0 to 1
    (conventions: Whittaker's beta of two records; ADR 0575)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    one = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0 or b_ > 0:
            one += 1
    return one / (2 * both + one)


def simpson_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Simpson's beta (turnover) of the records ``x`` and ``y`` of values at least 0, each with
    a value above 0: min(b, c)/(a + min(b, c)) on the kinds above 0, from 0 to 1
    (conventions: Simpson's beta of two records; ADR 0576)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    least = min(only_x, only_y)
    return least / (both + least)


def nestedness_beta(x: ArrayLike, y: ArrayLike) -> float:
    """The nestedness part of the Sorensen dissimilarity of the records ``x`` and ``y`` of
    values at least 0, each with a value above 0: whittaker_beta - simpson_beta, from 0 to 1
    (conventions: nestedness part of the Sorensen dissimilarity; ADR 0577)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    least = min(only_x, only_y)
    num = abs(only_x - only_y) * both
    return num / ((2 * both + only_x + only_y) * (both + least))


def jaccard_turnover(x: ArrayLike, y: ArrayLike) -> float:
    """The turnover part of the Jaccard dissimilarity of the records ``x`` and ``y`` of values
    at least 0, each with a value above 0: 2 min(b, c)/(a + 2 min(b, c)) on the kinds above 0,
    from 0 to 1 (conventions: turnover part of the Jaccard dissimilarity; ADR 0578)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    least = 2 * min(only_x, only_y)
    return least / (both + least)


def jaccard_nestedness(x: ArrayLike, y: ArrayLike) -> float:
    """The nestedness part of the Jaccard dissimilarity of the records ``x`` and ``y`` of
    values at least 0, each with a value above 0: (b + c)/(a + b + c) - jaccard_turnover,
    from 0 to 1 (conventions: nestedness part of the Jaccard dissimilarity; ADR 0579)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    least = 2 * min(only_x, only_y)
    num = abs(only_x - only_y) * both
    return num / ((both + only_x + only_y) * (both + least))


def ruzicka_similarity(x: ArrayLike, y: ArrayLike) -> float:
    """The Ruzicka similarity of the records ``x`` and ``y`` of values at least 0, each with a
    value above 0: sum(min(x, y))/sum(max(x, y)), from 0 to 1 (conventions: Ruzicka
    similarity of two records; ADR 0580)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    m = max(max(xv), max(yv))
    low = 0.0
    high = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        low += min(a_, b_) / m
        high += max(a_, b_) / m
    return low / high


def morisita_overlap(x: ArrayLike, y: ArrayLike) -> float:
    """Morisita's overlap of the count records ``x`` and ``y``, whole numbers at least 0, each
    totalling from 2 to 10 000 000: 2 sum(x y)/((l_x + l_y) X Y) with the unbiased Simpson
    concentrations l, at least 0 (conventions: Morisita's overlap of two count records;
    ADR 0581)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        if np.any(a != np.floor(a)):
            raise ValueError(f"{name} must be whole numbers")
        vals = [float(b) for b in a]
        total = 0.0
        for b in vals:
            total += b
        if total < 2:
            raise ValueError(f"{name} must total at least 2")
        if total > 10_000_000:
            raise ValueError(f"{name} must total at most 10 000 000")
        pair.append(vals)
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    big_x = 0.0
    big_y = 0.0
    cross = 0.0
    sx = 0.0
    sy = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        big_x += a_
        big_y += b_
        cross += a_ * b_
        sx += a_ * (a_ - 1.0)
        sy += b_ * (b_ - 1.0)
    den = sx * (big_y * (big_y - 1.0)) + sy * (big_x * (big_x - 1.0))
    if not den > 0:
        raise ValueError("x or y must hold a count above 1")
    return 2.0 * cross * (big_x - 1.0) * (big_y - 1.0) / den


def bray_curtis_balanced(x: ArrayLike, y: ArrayLike) -> float:
    """The balanced-variation part of the Bray-Curtis dissimilarity of the records ``x`` and
    ``y`` of values at least 0, each with a value above 0: min(B, C)/(A + min(B, C)), from 0
    to 1 (conventions: balanced-variation part of the Bray-Curtis dissimilarity; ADR 0582)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    m = max(max(xv), max(yv))
    shared = 0.0
    only_x = 0.0
    only_y = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        lo = min(a_, b_)
        shared += lo / m
        only_x += (a_ - lo) / m
        only_y += (b_ - lo) / m
    least = min(only_x, only_y)
    return least / (shared + least)


def bray_curtis_gradient(x: ArrayLike, y: ArrayLike) -> float:
    """The abundance-gradient part of the Bray-Curtis dissimilarity of the records ``x`` and
    ``y`` of values at least 0, each with a value above 0: bray_curtis - bray_curtis_balanced,
    from 0 to 1 (conventions: abundance-gradient part of the Bray-Curtis dissimilarity;
    ADR 0583)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    m = max(max(xv), max(yv))
    shared = 0.0
    only_x = 0.0
    only_y = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        lo = min(a_, b_)
        shared += lo / m
        only_x += (a_ - lo) / m
        only_y += (b_ - lo) / m
    least = min(only_x, only_y)
    num = abs(only_x - only_y) * shared
    return num / ((2.0 * shared + (only_x + only_y)) * (shared + least))


def podani_replacement(x: ArrayLike, y: ArrayLike) -> float:
    """Podani's replacement part of the Jaccard dissimilarity of the records ``x`` and ``y`` of
    values at least 0, each with a value above 0: 2 min(b, c)/(a + b + c) on the kinds above
    0, from 0 to 1 (conventions: Podani's replacement part of the Jaccard dissimilarity;
    ADR 0584)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    least = 2 * min(only_x, only_y)
    return least / (both + only_x + only_y)


def podani_richness_difference(x: ArrayLike, y: ArrayLike) -> float:
    """Podani's richness-difference part of the Jaccard dissimilarity of the records ``x`` and
    ``y`` of values at least 0, each with a value above 0: |b - c|/(a + b + c) on the kinds
    above 0, from 0 to 1 (conventions: Podani's richness-difference part of the Jaccard
    dissimilarity; ADR 0585)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    return abs(only_x - only_y) / (both + only_x + only_y)


def ruzicka_replacement(x: ArrayLike, y: ArrayLike) -> float:
    """The replacement part of the Ruzicka dissimilarity of the records ``x`` and ``y`` of
    values at least 0, each with a value above 0: 2 min(B, C)/(A + B + C), from 0 to 1
    (conventions: replacement part of the Ruzicka dissimilarity; ADR 0586)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    m = max(max(xv), max(yv))
    shared = 0.0
    only_x = 0.0
    only_y = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        lo = min(a_, b_)
        shared += lo / m
        only_x += (a_ - lo) / m
        only_y += (b_ - lo) / m
    return 2.0 * min(only_x, only_y) / (shared + (only_x + only_y))


def ruzicka_richness_difference(x: ArrayLike, y: ArrayLike) -> float:
    """The richness-difference part of the Ruzicka dissimilarity of the records ``x`` and
    ``y`` of values at least 0, each with a value above 0: |B - C|/(A + B + C), from 0 to 1
    (conventions: richness-difference part of the Ruzicka dissimilarity; ADR 0587)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    m = max(max(xv), max(yv))
    shared = 0.0
    only_x = 0.0
    only_y = 0.0
    for a_, b_ in zip(xv, yv, strict=True):
        lo = min(a_, b_)
        shared += lo / m
        only_x += (a_ - lo) / m
        only_y += (b_ - lo) / m
    return abs(only_x - only_y) / (shared + (only_x + only_y))


def podani_nestedness(x: ArrayLike, y: ArrayLike) -> float:
    """Podani's nestedness of the records ``x`` and ``y`` of values at least 0, each with a
    value above 0: (a + |b - c|)/(a + b + c) on the kinds above 0 when a > 0, else 0, from 0
    to 1 (conventions: Podani's nestedness; ADR 0588)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    if both == 0:
        return 0.0
    return (both + abs(only_x - only_y)) / (both + only_x + only_y)


def harrison_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Harrison's beta of the records ``x`` and ``y`` of values at least 0, each with a value
    above 0: min(b, c)/(a + max(b, c)) on the kinds above 0, from 0 to 1 (conventions:
    Harrison's beta; ADR 0589)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    return min(only_x, only_y) / (both + max(only_x, only_y))


def cody_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Cody's beta of the records ``x`` and ``y`` of values at least 0, each with a value
    above 0: (b + c)/2 on the kinds above 0, the mean of the kinds gained and lost, from 0 to
    the record length (conventions: Cody's beta; ADR 0590)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            continue
        if a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    return (only_x + only_y) / 2.0


def wilson_shmida_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Wilson and Shmida's beta of the records ``x`` and ``y`` of values at least 0, each with
    a value above 0: (b + c)/(2a + b + c) on the kinds above 0, from 0 to 1 (conventions:
    Wilson and Shmida's beta; ADR 0591)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    return (only_x + only_y) / (2 * both + only_x + only_y)


def magurran_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Magurran's beta of the records ``x`` and ``y`` of values at least 0, each with a value
    above 0: (2a + b + c)(1 - a/(a + b + c)) on the kinds above 0, from 0 to twice the record
    length (conventions: Magurran's beta; ADR 0592)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    unshared = only_x + only_y
    return (2 * both + unshared) * unshared / (both + unshared)


def williams_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Williams' beta of the records ``x`` and ``y`` of values at least 0, each with a value
    above 0: min(b, c)/(a + b + c) on the kinds above 0, from 0 to 1/2 (conventions:
    Williams' beta; ADR 0593)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    return min(only_x, only_y) / (both + only_x + only_y)


def lennon_gradient_beta(x: ArrayLike, y: ArrayLike) -> float:
    """Lennon's gradient beta of the records ``x`` and ``y`` of values at least 0, each with a
    value above 0: 2|b - c|/(2a + b + c) on the kinds above 0, from 0 to below 2
    (conventions: Lennon's gradient beta; ADR 0594)."""
    pair = []
    for name, v in (("x", x), ("y", y)):
        a = np.asarray(v)
        if a.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        if np.iscomplexobj(a):
            raise ValueError(f"{name} must be real")
        a = a.astype(np.float64, copy=False)
        if a.size < 1:
            raise ValueError(f"{name} must not be empty")
        if not np.all(np.isfinite(a)) or np.any(a < 0):
            raise ValueError(f"{name} must be finite and at least 0")
        top = float(np.max(a))
        if not top > 0:
            raise ValueError(f"{name} must have a value above 0")
        pair.append([float(b) for b in a])
    xv, yv = pair
    if len(xv) != len(yv):
        raise ValueError("x and y must have the same length")
    both = 0
    only_x = 0
    only_y = 0
    for a_, b_ in zip(xv, yv, strict=True):
        if a_ > 0 and b_ > 0:
            both += 1
        elif a_ > 0:
            only_x += 1
        elif b_ > 0:
            only_y += 1
    return 2 * abs(only_x - only_y) / (2 * both + only_x + only_y)


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
