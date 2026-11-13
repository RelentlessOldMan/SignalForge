"""Power measurements and tone metrics. Definitions in docs/conventions.md."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from . import spectral
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
    if np.asarray(samples).size < 2:
        raise ValueError("tone metrics need at least two samples")
    harmonics = count(num_harmonics, "num_harmonics")
    w_given = None if width is None else count(width, "width")
    given = None if fundamental is None else real(fundamental, "fundamental")
    d = spectral.welch_psd(samples, sample_rate, window=window, beta=beta)
    fs = d.sample_rate
    if given is not None and not (abs(given) <= fs / 2 and (given >= 0 or not d.one_sided)):
        raise ValueError(
            "fundamental must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)"
        )
    w = _half_width(window, beta) if w_given is None else w_given
    p = d.psd * d.bin_width
    f = d.frequencies
    m = p.size
    claimed = np.zeros(m, dtype=bool)

    def nearest(freq: float) -> int:
        return min(max(math.floor((freq - float(f[0])) / d.bin_width + 0.5), 0), m - 1)

    def group(c: int) -> NDArray[np.intp]:
        idx = np.arange(max(c - w, 0), min(c + w, m - 1) + 1)
        free: NDArray[np.intp] = idx[~claimed[idx]]
        claimed[free] = True
        return free

    dc = group(nearest(0.0))
    if given is None:
        free = np.flatnonzero(~claimed)
        if free.size == 0:
            raise ValueError("no bins are left for the fundamental after the DC group")
        c = int(free[np.argmax(p[free])])
    else:
        c = nearest(given)
        if claimed[c]:
            raise ValueError("the fundamental falls in the DC group")
    fund = group(c)
    signal = float(np.sum(p[fund]))
    if not signal > 0:
        raise ValueError("no signal power at the fundamental")
    f1 = float(np.sum(p[fund] * f[fund])) / signal
    harmonic = 0.0
    for h in range(2, harmonics + 2):
        if d.one_sided:
            g = (h * f1) % fs
            g = fs - g if g > fs / 2 else g
        else:
            g = (h * f1 + fs / 2) % fs - fs / 2
        harmonic += float(np.sum(p[group(nearest(g))]))
    noise = float(np.sum(p[~claimed]))
    sinad = _db(signal, noise + harmonic)
    return ToneMetrics(
        fundamental_frequency=f1,
        signal_power=signal,
        harmonic_power=harmonic,
        noise_power=noise,
        dc_power=float(np.sum(p[dc])),
        snr_db=_db(signal, noise),
        sinad_db=sinad,
        thd_db=-_db(signal, harmonic),
        enob=(sinad - 10 * math.log10(1.5)) / (20 * math.log10(2)),
    )


def _half_width(window: str, beta: float | None) -> int:
    if window == "kaiser":
        if beta is None:
            raise ValueError("the kaiser window needs beta")
        return math.ceil(math.sqrt(1 + (beta / math.pi) ** 2))
    return len(spectral._COSINE_SUMS[window])


def _db(num: float, den: float) -> float:
    """10*log10(num/den) for num > 0; +inf when den is zero."""
    return math.inf if den == 0 else 10 * math.log10(num / den)
