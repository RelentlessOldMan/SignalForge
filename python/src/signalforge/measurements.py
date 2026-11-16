"""Power measurements and tone metrics. Definitions in docs/conventions.md."""

from __future__ import annotations

import math
from collections.abc import Callable
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


@dataclass(frozen=True, eq=False)
class PowerCcdf:
    """Fraction of samples whose instantaneous power exceeds the mean by each level (conventions:
    Power CCDF; ADR 0119)."""

    mean_power: float
    levels_db: NDArray[np.float64]
    probabilities: NDArray[np.float64]


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
