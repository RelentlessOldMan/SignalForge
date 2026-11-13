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
        d = spectral.welch_psd(samples, sample_rate, window=window, beta=beta)
        fs = d.sample_rate
        if given is not None and not (abs(given) <= fs / 2 and (given >= 0 or not d.one_sided)):
            raise ValueError(
                "fundamental must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)"
            )
        self.d = d
        self.w = _half_width(window, beta) if w_given is None else w_given
        self.p: NDArray[np.float64] = d.psd * d.bin_width
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


def _half_width(window: str, beta: float | None) -> int:
    if window == "kaiser":
        if beta is None:
            raise ValueError("the kaiser window needs beta")
        return math.ceil(math.sqrt(1 + (beta / math.pi) ** 2))
    return len(spectral._COSINE_SUMS[window])


def _db(num: float, den: float) -> float:
    """10*log10(num/den) for num > 0; +inf when den is zero."""
    return math.inf if den == 0 else 10 * math.log10(num / den)
