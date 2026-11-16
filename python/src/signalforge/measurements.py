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
    imd_f = [g.alias(2 * lo - hi), g.alias(2 * hi - lo)]
    imd_p = []
    for x in imd_f:
        k = g.nearest(x)
        if g.claimed[k]:
            raise ValueError("an intermodulation product falls on DC, a tone or the other product")
        imd_p.append(g.power(g.group(k)))
    pt = (g.signal + p2) / 2
    dbc = [10 * math.log10(p / pt) if p > 0 else -math.inf for p in imd_p]
    worst = max(dbc)
    return TwoToneImd(
        tone_frequencies=np.array([g.f1, g.centroid(idx, p2)], dtype=np.float64),
        tone_powers=np.array([g.signal, p2], dtype=np.float64),
        imd_frequencies=np.array(imd_f, dtype=np.float64),
        imd_powers=np.array(imd_p, dtype=np.float64),
        imd_dbc=np.array(dbc, dtype=np.float64),
        worst_imd_dbc=worst,
        ip3_db=10 * math.log10(pt) - worst / 2,
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
) -> PhaseNoise:
    """``L(f)`` in dBc/Hz at each offset from the strongest bin (or the one at ``carrier``), from
    a Welch PSD (conventions: Phase noise measurement; ADR 0108)."""
    off = np.asarray(offsets, dtype=np.float64)
    if off.ndim != 1 or off.size == 0:
        raise ValueError("offsets must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(off) & (off > 0)):
        raise ValueError("offsets must be finite and positive")
    if np.asarray(samples).size < 2:
        raise ValueError("phase noise needs at least two samples")
    seg = None if nperseg is None else count(nperseg, "nperseg")
    w_given = None if width is None else count(width, "width")
    given = None if carrier is None else real(carrier, "carrier")
    with np.errstate(over="ignore"):  # an overflowing spectrum is rejected below
        d = spectral.welch_psd(samples, sample_rate, nperseg=seg, window=window, beta=beta)
    fs = d.sample_rate
    psd = d.psd
    p = psd * d.bin_width
    if not math.isfinite(float(np.sum(p))):
        raise ValueError("samples must be finite and small enough for a finite spectrum")
    w = _half_width(window, beta) if w_given is None else w_given

    def nearest(freq: float) -> int:
        k = math.floor((freq - float(d.frequencies[0])) / d.bin_width + 0.5)
        return min(max(k, 0), psd.size - 1)

    if given is None:
        c = int(np.argmax(psd))
    else:
        if not (abs(given) <= fs / 2 and (given >= 0 or not d.one_sided)):
            raise ValueError(
                "carrier must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)"
            )
        if not d.one_sided:
            given = (given + fs / 2) % fs - fs / 2  # +fs/2 is the bin at -fs/2
        c = nearest(given)
    group = slice(max(c - w, 0), min(c + w, psd.size - 1) + 1)
    pc = float(np.sum(p[group]))
    if not pc > 0:
        raise ValueError("no power at the carrier")
    fc = float(np.sum(p[group] * d.frequencies[group])) / pc
    lo = 0.0 if d.one_sided else -fs / 2
    out = np.empty(off.size)
    for i, o in enumerate(off.tolist()):
        if not (fc - o >= lo and (fc + o <= fs / 2 if d.one_sided else fc + o < fs / 2)):
            raise ValueError("an offset reaches past the spectrum")
        ka, kb = nearest(fc - o), nearest(fc + o)
        if abs(ka - c) <= w or abs(kb - c) <= w:
            raise ValueError("an offset falls in the carrier group")
        s = (float(psd[ka]) + float(psd[kb])) / 2
        out[i] = 10 * math.log10(s / pc) if s > 0 else -math.inf
    return PhaseNoise(fc, pc, off.copy(), out)


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
