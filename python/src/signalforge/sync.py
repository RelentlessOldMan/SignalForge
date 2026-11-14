"""Synchronization: block estimators of symbol timing, QPSK carrier frequency and phase, and
tracking loops.

Definitions are in docs/conventions.md (Synchronization) and
docs/adr/0008-block-synchronization.md.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from . import modulation as _mod
from ._checks import count, real
from .channel import _interpolate
from .modulation import _INV_SQRT10, _QAM16_THRESHOLD


def _complex(x: ArrayLike, what: str, minimum: int) -> NDArray[np.complex128]:
    a = np.asarray(x)
    if a.ndim != 1:
        raise ValueError(f"{what} must be one-dimensional")
    if a.size < minimum:
        raise ValueError(f"{what} needs at least {minimum}")
    a = np.asarray(a, dtype=np.complex128)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{what} must be finite")
    # The estimates do not depend on scale. Scaling by a power of two is exact and keeps |z|^4
    # from overflowing or underflowing.
    m = float(np.max(np.maximum(np.abs(a.real), np.abs(a.imag)), initial=0.0))
    if m > 0:
        e = -math.frexp(m)[1]
        a = np.ldexp(a.real, e) + 1j * np.ldexp(a.imag, e)
    return np.asarray(a, dtype=np.complex128)


def _arg(s: complex) -> float:
    """Phase in ``(-pi, pi]``; 0 for an exact zero (atan2 gives -pi for a -0.0 imaginary part)."""
    if s == 0:
        return 0.0
    a = math.atan2(s.imag, s.real)
    return math.pi if a == -math.pi else a


def timing_offset(samples: ArrayLike, samples_per_symbol: int) -> float:
    """Oerder-Meyr symbol timing estimate in samples, in ``[0, sps)``."""
    sps = count(samples_per_symbol, "samples_per_symbol")
    if sps < 2:
        raise ValueError("samples_per_symbol must be at least 2")
    y = _complex(samples, "samples", 1)
    n = np.arange(y.size)
    s = complex(np.sum((y.real**2 + y.imag**2) * np.exp(-2j * np.pi * (n % sps) / sps)))
    tau = -sps * _arg(s) / (2 * math.pi)
    if tau < 0:
        tau += sps
    return 0.0 if tau >= sps else tau


def qpsk_frequency_offset(symbols: ArrayLike, symbol_rate: float) -> float:
    """Carrier frequency offset of QPSK symbols in Hz, in ``(-Rs/8, Rs/8]``."""
    if not 0 < symbol_rate < math.inf:
        raise ValueError("symbol_rate must be positive and finite")
    z = _complex(symbols, "symbols", 2)
    z2 = z * z
    w = z2 * z2
    s = complex(np.sum(w[1:] * np.conj(w[:-1])))
    return _arg(s) * symbol_rate / (8 * math.pi)


def power_frequency_offset(symbols: ArrayLike, symbol_rate: float, power: int) -> float:
    """Carrier frequency offset in Hz from the peak of the spectrum of ``z**power``.

    In ``(-Rs/(2p), Rs/(2p)]``. Works for any constellation whose ``power``-th power has a non-zero
    mean: QPSK and 16-QAM at 4, 8-PSK at 8.
    """
    if not 0 < symbol_rate < math.inf:
        raise ValueError("symbol_rate must be positive and finite")
    p = count(power, "power")
    if not 1 <= p <= 16:
        raise ValueError("power must be from 1 to 16")
    z = _complex(symbols, "symbols", 2)
    w = z.copy()
    for _ in range(p - 1):
        w = w * z
    n = w.size
    big = 1
    while big < 4 * n:
        big *= 2
    spectrum = np.fft.fft(w, big)
    pw = spectrum.real**2 + spectrum.imag**2
    if not np.any(pw > 0):
        return 0.0
    i = int(np.argmax(pw))
    if i > big // 2:
        i -= big
    k = np.arange(n, dtype=np.float64)

    def slope(nu: float) -> float:
        a = (-2 * math.pi * nu) * k
        e = np.cos(a) + 1j * np.sin(a)
        s = complex(np.sum(w * e))
        t = complex(np.sum(k * w * e))
        return s.real * t.imag - s.imag * t.real

    lo, hi = (i - 1) / big, (i + 1) / big
    for _ in range(60):
        m = (lo + hi) / 2
        if slope(m) > 0:
            lo = m
        else:
            hi = m
    nu = (lo + hi) / 2
    if nu > 0.5:
        nu -= 1
    elif nu <= -0.5:
        nu += 1
    return nu * symbol_rate / p


def qpsk_phase_offset(symbols: ArrayLike) -> float:
    """Carrier phase of QPSK symbols in radians, in ``(-pi/4, pi/4]``, modulo pi/2."""
    z = _complex(symbols, "symbols", 1)
    z2 = z * z
    w = z2 * z2
    return _arg(-complex(np.sum(w))) / 4


def qpsk_block_phases(symbols: ArrayLike, block_symbols: int) -> NDArray[np.float64]:
    """QPSK carrier phase of each block of ``block_symbols`` symbols, unwrapped in steps of pi/2.

    The first block's phase is in ``(-pi/4, pi/4]``; each later one is moved by a multiple of pi/2
    to within pi/4 of the one before. A last, shorter block is included.
    """
    b = count(block_symbols, "block_symbols")
    if b < 1:
        raise ValueError("block_symbols must be at least 1")
    z = _complex(symbols, "symbols", 1)
    out = np.empty((z.size + b - 1) // b)
    for i in range(out.size):
        phi = qpsk_phase_offset(z[i * b : (i + 1) * b])
        if i > 0:
            phi += (math.pi / 2) * round((out[i - 1] - phi) / (math.pi / 2))
        out[i] = phi
    return out


def psk8_phase_offset(symbols: ArrayLike) -> float:
    """Carrier phase of 8-PSK symbols in radians, in ``(-pi/8, pi/8]``, modulo pi/4."""
    z = _complex(symbols, "symbols", 1)
    z2 = z * z
    z4 = z2 * z2
    return _arg(complex(np.sum(z4 * z4))) / 8


def psk8_block_phases(symbols: ArrayLike, block_symbols: int) -> NDArray[np.float64]:
    """8-PSK carrier phase of each block of ``block_symbols`` symbols, unwrapped in steps of pi/4.

    The first block's phase is in ``(-pi/8, pi/8]``; each later one is moved by a multiple of pi/4
    to within pi/8 of the one before. A last, shorter block is included.
    """
    b = count(block_symbols, "block_symbols")
    if b < 1:
        raise ValueError("block_symbols must be at least 1")
    z = _complex(symbols, "symbols", 1)
    out = np.empty((z.size + b - 1) // b)
    for i in range(out.size):
        phi = psk8_phase_offset(z[i * b : (i + 1) * b])
        if i > 0:
            phi += (math.pi / 4) * round((out[i - 1] - phi) / (math.pi / 4))
        out[i] = phi
    return out


def pi_loop_gains(
    loop_bandwidth: float, damping: float, detector_gain: float
) -> tuple[float, float]:
    """``(kp, ki)`` of a second-order loop with noise bandwidth ``loop_bandwidth`` per update
    (conventions: Synchronization, Tracking loops)."""
    bn = real(loop_bandwidth, "loop_bandwidth")
    z = real(damping, "damping")
    kd = real(detector_gain, "detector_gain")
    if not 0 < bn < 0.5:
        raise ValueError("loop_bandwidth must be in (0, 0.5)")
    if not z > 0 or not kd > 0:
        raise ValueError("damping and detector_gain must be positive")
    theta = bn / (z + 1 / (4 * z))
    d = 1 + 2 * z * theta + theta * theta
    return 4 * z * theta / d / kd, 4 * theta * theta / d / kd


@dataclass(frozen=True)
class TimingRecovery:
    """What a timing loop took: the symbols, their positions in samples, the detector output."""

    symbols: NDArray[np.complex128]
    positions: NDArray[np.float64]
    errors: NDArray[np.float64]


def gardner_timing(
    samples: ArrayLike,
    samples_per_symbol: int,
    kp: float,
    ki: float,
    *,
    start: float = 0.0,
    half_width: int = 8,
) -> TimingRecovery:
    """Gardner timing recovery: a PI loop on the step between symbols, reading between samples
    by the fractional-delay kernel (conventions: Synchronization, Tracking loops)."""
    sps = count(samples_per_symbol, "samples_per_symbol")
    if sps < 2:
        raise ValueError("samples_per_symbol must be at least 2")
    y = np.asarray(samples)
    if y.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    y = np.asarray(y, dtype=np.complex128)
    if not np.all(np.isfinite(y)):
        raise ValueError("samples must be finite")
    p = real(kp, "kp")
    i = real(ki, "ki")
    tau = real(start, "start")
    if p < 0 or i < 0 or tau < 0:
        raise ValueError("kp, ki and start must not be negative")
    h = count(half_width, "half_width")
    if h < 1:
        raise ValueError("half_width must be at least 1")
    ys: list[complex] = y.tolist()
    symbols: list[complex] = []
    positions: list[float] = []
    errors: list[float] = []
    v = 0.0
    while tau <= len(ys) - 1:
        z = _interpolate(ys, tau, h)
        e = 0.0
        if symbols:
            mid = _interpolate(ys, (positions[-1] + tau) / 2, h)
            delta = z - symbols[-1]
            e = mid.real * delta.real + mid.imag * delta.imag
        symbols.append(z)
        positions.append(tau)
        errors.append(e)
        v += i * e
        step = min(max(sps - p * e - v, sps / 2), 3 * sps / 2)
        tau += step
    return TimingRecovery(
        np.array(symbols, dtype=np.complex128),
        np.array(positions, dtype=np.float64),
        np.array(errors, dtype=np.float64),
    )


@dataclass(frozen=True)
class CarrierRecovery:
    """What a carrier loop gave: the corrected symbols, the phase used for each, the detector
    output."""

    symbols: NDArray[np.complex128]
    phases: NDArray[np.float64]
    errors: NDArray[np.float64]


def _carrier_loop(
    symbols: ArrayLike,
    kp: float,
    ki: float,
    phase: float,
    decide: Callable[[float, float], tuple[float, float]],
) -> CarrierRecovery:
    """The decision-directed PI loop shared by the carrier trackers; ``decide`` gives ``d``."""
    z = np.asarray(symbols)
    if z.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    z = np.asarray(z, dtype=np.complex128)
    if not np.all(np.isfinite(z)):
        raise ValueError("symbols must be finite")
    p = real(kp, "kp")
    i = real(ki, "ki")
    phi = real(phase, "phase")
    if p < 0 or i < 0:
        raise ValueError("kp and ki must not be negative")
    out: list[complex] = []
    phases: list[float] = []
    errors: list[float] = []
    v = 0.0
    for x in z.tolist():
        c = math.cos(phi)
        s = math.sin(phi)
        re = x.real * c + x.imag * s
        im = x.imag * c - x.real * s
        dre, dim = decide(re, im)
        e = dre * im - dim * re
        out.append(complex(re, im))
        phases.append(phi)
        errors.append(e)
        v += i * e
        phi = phi + p * e + v
    return CarrierRecovery(
        np.array(out, dtype=np.complex128),
        np.array(phases, dtype=np.float64),
        np.array(errors, dtype=np.float64),
    )


def _qpsk_decision(re: float, im: float) -> tuple[float, float]:
    return (1.0 if re >= 0 else -1.0, 1.0 if im >= 0 else -1.0)


_C8 = 1 / math.sqrt(2)
_PSK8_POINTS = [(1.0, 0.0), (_C8, _C8), (0.0, 1.0), (-_C8, _C8),
                (-1.0, 0.0), (-_C8, -_C8), (0.0, -1.0), (_C8, -_C8)]  # fmt: skip


def _psk8_decision(re: float, im: float) -> tuple[float, float]:
    return _PSK8_POINTS[math.floor(math.atan2(im, re) / (math.pi / 4) + 0.5) % 8]


def _qam16_level(v: float) -> float:
    m = 1.0 if abs(v) < _QAM16_THRESHOLD else 3.0
    return (m if v >= 0 else -m) * _INV_SQRT10


def _qam16_decision(re: float, im: float) -> tuple[float, float]:
    return (_qam16_level(re), _qam16_level(im))


_INV_SQRT42 = 1.0 / math.sqrt(42.0)
_QAM64_T2 = 2.0 / math.sqrt(42.0)
_QAM64_T4 = 4.0 / math.sqrt(42.0)
_QAM64_T6 = 6.0 / math.sqrt(42.0)


def _qam64_level(v: float) -> float:
    a = abs(v)
    m = 4.0 + (-1.0 if a < _QAM64_T4 else 1.0) * (1.0 if _QAM64_T2 < a < _QAM64_T6 else 3.0)
    return (-m if v < 0 else m) * _INV_SQRT42


def _qam64_decision(re: float, im: float) -> tuple[float, float]:
    return (_qam64_level(re), _qam64_level(im))


def qpsk_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed QPSK carrier loop: a PI loop on the phase, one update per symbol
    (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _qpsk_decision)


def psk8_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed 8-PSK carrier loop (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _psk8_decision)


def qam16_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed 16-QAM carrier loop (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _qam16_decision)


def qam64_carrier_tracking(
    symbols: ArrayLike, kp: float, ki: float, *, phase: float = 0.0
) -> CarrierRecovery:
    """Decision-directed 64-QAM carrier loop (conventions: Synchronization, Tracking loops)."""
    return _carrier_loop(symbols, kp, ki, phase, _qam64_decision)


@dataclass(frozen=True)
class Equalization:
    """What an equalizer gave: the output symbols, the error each update used, the final taps."""

    symbols: NDArray[np.complex128]
    errors: NDArray[np.complex128]
    taps: NDArray[np.complex128]


_DECISIONS: dict[str, tuple[Callable[[ArrayLike], NDArray[np.uint8]], Callable[..., Any]]] = {
    "qpsk": (_mod.qpsk_demap_hard, _mod.qpsk_map),
    "psk8": (_mod.psk8_demap_hard, _mod.psk8_map),
    "qam16": (_mod.qam16_demap_hard, _mod.qam16_map),
    "qam64": (_mod.qam64_demap_hard, _mod.qam64_map),
}


def lms_equalizer(
    samples: ArrayLike,
    training: ArrayLike,
    num_taps: int,
    step: float,
    *,
    samples_per_symbol: int = 1,
    center: int | None = None,
    decision: str | None = None,
    initial_taps: ArrayLike | None = None,
) -> Equalization:
    """Normalized LMS equalizer, fractionally spaced, trained on known symbols and then on its own
    decisions (conventions: Synchronization, LMS equalizer; ADR 0066). ``initial_taps`` replaces
    the unit impulse it starts from (ADR 0072)."""
    out, errors, w, _ = _equalize(
        samples, training, num_taps, 0, step, samples_per_symbol, center, decision, initial_taps
    )
    return Equalization(out, errors, w)


def rls_equalizer(
    samples: ArrayLike,
    training: ArrayLike,
    num_taps: int,
    forgetting: float,
    *,
    delta: float = 0.01,
    samples_per_symbol: int = 1,
    center: int | None = None,
    decision: str | None = None,
    initial_taps: ArrayLike | None = None,
) -> Equalization:
    """Exponentially weighted recursive-least-squares equalizer, fractionally spaced, trained on
    known symbols and then on its own decisions (conventions: Synchronization, RLS equalizer; ADR
    0076). Converges in a few times ``num_taps`` symbols however the channel is conditioned."""
    xs, ts, taps, _, sps, c = _equalizer_args(
        samples, training, num_taps, 0, samples_per_symbol, center
    )
    lam = real(forgetting, "forgetting")
    if not 0 < lam <= 1:
        raise ValueError("forgetting must be in (0, 1]")
    dl = real(delta, "delta")
    if not dl > 0:
        raise ValueError("delta must be above 0")
    if decision is not None and decision not in _DECISIONS:
        raise ValueError(f"decision must be None or one of {sorted(_DECISIONS)}")
    w = [0j] * taps
    w[c] = 1 + 0j
    if initial_taps is not None:
        w = _start(initial_taps, taps, "initial_taps")
    pm = [[(1 / dl if i == j else 0.0) + 0j for j in range(taps)] for i in range(taps)]
    out: list[complex] = []
    errors: list[complex] = []
    for n in range(-(-len(xs) // sps)):
        base = n * sps + c
        u = [xs[base - i] if 0 <= base - i < len(xs) else 0j for i in range(taps)]
        y = 0j
        for wi, ui in zip(w, u, strict=True):
            y += wi * ui
        out.append(y)
        if n < len(ts):
            d: complex | None = ts[n]
        elif decision is not None:
            demap, mapper = _DECISIONS[decision]
            d = complex(mapper(demap(np.array([y])))[0])
        else:
            d = None
        if d is None:
            errors.append(0j)
            continue
        e = d - y
        errors.append(e)
        p = 0.0
        for ui in u:
            p += ui.real * ui.real + ui.imag * ui.imag
        if not p > 0:
            continue
        q = []
        for row in pm:
            qi = 0j
            for pij, uj in zip(row, u, strict=True):
                qi += pij * uj.conjugate()
            q.append(qi)
        s = complex(lam)
        for ui, qi in zip(u, q, strict=True):
            s += ui * qi
        g = [qi / s for qi in q]
        w = [wi + gi * e for wi, gi in zip(w, g, strict=True)]
        r = []
        for j in range(taps):
            rj = 0j
            for i in range(taps):
                rj += u[i] * pm[i][j]
            r.append(rj)
        pm = [[(pm[i][j] - g[i] * r[j]) / lam for j in range(taps)] for i in range(taps)]
    return Equalization(
        np.array(out, dtype=np.complex128),
        np.array(errors, dtype=np.complex128),
        np.array(w, dtype=np.complex128),
    )


def cma_equalizer(
    samples: ArrayLike,
    num_taps: int,
    step: float,
    *,
    samples_per_symbol: int = 1,
    center: int | None = None,
    modulus: float = 1.0,
    initial_taps: ArrayLike | None = None,
) -> Equalization:
    """Blind constant-modulus equalizer, normalized, fractionally spaced; its output keeps the
    channel's phase (conventions: Synchronization, Constant-modulus equalizer; ADR 0074)."""
    xs, _, taps, _, sps, c = _equalizer_args(samples, [], num_taps, 0, samples_per_symbol, center)
    mu = real(step, "step")
    if not 0 <= mu <= 2:
        raise ValueError("step must be between 0 and 2")
    rr = real(modulus, "modulus")
    if not rr > 0:
        raise ValueError("modulus must be above 0")
    w = [0j] * taps
    w[c] = 1 + 0j
    if initial_taps is not None:
        w = _start(initial_taps, taps, "initial_taps")
    out: list[complex] = []
    errors: list[complex] = []
    for n in range(-(-len(xs) // sps)):
        base = n * sps + c
        u = [xs[base - i] if 0 <= base - i < len(xs) else 0j for i in range(taps)]
        y = 0j
        for wi, ui in zip(w, u, strict=True):
            y += wi * ui
        out.append(y)
        e = y * (rr - (y.real * y.real + y.imag * y.imag))
        errors.append(e)
        p = 0.0
        for ui in u:
            p += ui.real * ui.real + ui.imag * ui.imag
        if p > 0:
            g = mu / p
            w = [wi + g * e * ui.conjugate() for wi, ui in zip(w, u, strict=True)]
    return Equalization(
        np.array(out, dtype=np.complex128),
        np.array(errors, dtype=np.complex128),
        np.array(w, dtype=np.complex128),
    )


@dataclass(frozen=True)
class DfeEqualization:
    """What a decision-feedback equalizer gave: the output symbols, the error each update used, the
    final forward taps and the final feedback taps."""

    symbols: NDArray[np.complex128]
    errors: NDArray[np.complex128]
    taps: NDArray[np.complex128]
    feedback_taps: NDArray[np.complex128]


def dfe_equalizer(
    samples: ArrayLike,
    training: ArrayLike,
    num_taps: int,
    num_feedback: int,
    step: float,
    *,
    samples_per_symbol: int = 1,
    center: int | None = None,
    decision: str | None = None,
    initial_taps: ArrayLike | None = None,
    initial_feedback: ArrayLike | None = None,
    phase_loop_gains: tuple[float, float] | None = None,
    pilots: ArrayLike | None = None,
    pilot_interval: int | None = None,
    slip_window: int = 2,
    forgetting: float | None = None,
    delta: float = 0.01,
) -> DfeEqualization:
    """Decision-feedback equalizer: the LMS equalizer plus feedback taps on the past references,
    one normalized LMS update over both (conventions: Synchronization, Decision-feedback
    equalizer; ADR 0069). ``initial_taps`` and ``initial_feedback`` replace the unit impulse and
    the zeros it starts from (ADR 0072). ``phase_loop_gains`` ``(kp, ki)`` adds a second-order
    carrier loop on the forward part (ADR 0073); ``pilots`` every ``pilot_interval`` outputs
    after the training are references and correct its cycle slips (ADR 0075). With
    ``forgetting`` the update is recursive least squares over both, ``delta`` its start (ADR
    0077)."""
    out, errors, w, b = _equalize(
        samples,
        training,
        num_taps,
        num_feedback,
        step,
        samples_per_symbol,
        center,
        decision,
        initial_taps,
        initial_feedback,
        phase_loop_gains,
        pilots,
        pilot_interval,
        slip_window,
        forgetting,
        delta,
    )
    return DfeEqualization(out, errors, w, b)


@dataclass(frozen=True)
class DfeTaps:
    """Equalizer taps: the forward taps and the feedback taps."""

    taps: NDArray[np.complex128]
    feedback_taps: NDArray[np.complex128]


def dfe_least_squares(
    samples: ArrayLike,
    training: ArrayLike,
    num_taps: int,
    num_feedback: int,
    *,
    samples_per_symbol: int = 1,
    center: int | None = None,
) -> DfeTaps:
    """The forward and feedback taps that minimize the squared error over the training, by
    Gaussian elimination on the normal equations (conventions: Synchronization, Least-squares
    equalizer taps; ADR 0072)."""
    xs, ts, taps, m, sps, c = _equalizer_args(
        samples, training, num_taps, num_feedback, samples_per_symbol, center
    )
    k_all = taps + m
    if len(ts) < k_all:
        raise ValueError("training needs at least num_taps + num_feedback symbols")
    g = [[0j] * k_all for _ in range(k_all)]
    h = [0j] * k_all
    for n, tn in enumerate(ts):
        base = n * sps + c
        v = [xs[base - i] if 0 <= base - i < len(xs) else 0j for i in range(taps)]
        v += [ts[n - j] if n - j >= 0 else 0j for j in range(1, m + 1)]
        for k in range(k_all):
            ck = v[k].conjugate()
            row = g[k]
            for col in range(k_all):
                row[col] += ck * v[col]
            h[k] += ck * tn
    for k in range(k_all):
        r, big = k, -1.0
        for i in range(k, k_all):
            mag = g[i][k].real * g[i][k].real + g[i][k].imag * g[i][k].imag
            if mag > big:
                r, big = i, mag
        if big == 0:
            raise ValueError("the training does not determine the taps")
        g[k], g[r] = g[r], g[k]
        h[k], h[r] = h[r], h[k]
        for i in range(k + 1, k_all):
            f = g[i][k] / g[k][k]
            for col in range(k + 1, k_all):
                g[i][col] -= f * g[k][col]
            h[i] -= f * h[k]
    th = [0j] * k_all
    for k in range(k_all - 1, -1, -1):
        acc = h[k]
        for col in range(k + 1, k_all):
            acc -= g[k][col] * th[col]
        th[k] = acc / g[k][k]
    th_a = np.array(th, dtype=np.complex128)
    return DfeTaps(th_a[:taps], th_a[taps:])


def _equalize(
    samples: ArrayLike,
    training: ArrayLike,
    num_taps: int,
    num_feedback: int,
    step: float,
    samples_per_symbol: int,
    center: int | None,
    decision: str | None,
    initial_taps: ArrayLike | None = None,
    initial_feedback: ArrayLike | None = None,
    phase_loop_gains: tuple[float, float] | None = None,
    pilots: ArrayLike | None = None,
    pilot_interval: int | None = None,
    slip_window: int = 2,
    forgetting: float | None = None,
    delta: float = 0.01,
) -> tuple[
    NDArray[np.complex128], NDArray[np.complex128], NDArray[np.complex128], NDArray[np.complex128]
]:
    xs, ts, taps, m, sps, c = _equalizer_args(
        samples, training, num_taps, num_feedback, samples_per_symbol, center
    )
    mu = real(step, "step")
    if not 0 <= mu <= 2:
        raise ValueError("step must be between 0 and 2")
    if decision is not None and decision not in _DECISIONS:
        raise ValueError(f"decision must be None or one of {sorted(_DECISIONS)}")
    n_out = -(-len(xs) // sps)
    if m > 0 and decision is None and len(ts) < n_out:
        raise ValueError("with num_feedback, decision must be given or training cover every output")
    w = [0j] * taps
    w[c] = 1 + 0j
    if initial_taps is not None:
        w = _start(initial_taps, taps, "initial_taps")
    fb = [0j] * m
    if initial_feedback is not None:
        fb = _start(initial_feedback, m, "initial_feedback")
    loop = None
    if phase_loop_gains is not None:
        if isinstance(phase_loop_gains, str | bytes) or len(phase_loop_gains) != 2:
            raise ValueError("phase_loop_gains must be None or a pair (kp, ki)")
        kp = real(phase_loop_gains[0], "phase_loop_gains")
        ki = real(phase_loop_gains[1], "phase_loop_gains")
        if kp < 0 or ki < 0:
            raise ValueError("phase_loop_gains must not be negative")
        loop = (kp, ki)
    if (pilots is None) != (pilot_interval is None):
        raise ValueError("pilots and pilot_interval go together")
    k_p = 0
    g_p: list[complex] = []
    window = count(slip_window, "slip_window")
    if window < 1:
        raise ValueError("slip_window must be at least 1")
    sigma = math.pi / 4 if decision == "psk8" else math.pi / 2
    if pilots is not None and pilot_interval is not None:
        k_p = count(pilot_interval, "pilot_interval")
        if k_p < 1:
            raise ValueError("pilot_interval must be at least 1")
        if loop is None or decision is None:
            raise ValueError("pilots need phase_loop_gains and decision")
        g_p = _start(pilots, max(n_out - len(ts), 0) // k_p, "pilots")
    lam = 0.0
    q_m: list[list[complex]] = []
    if forgetting is not None:
        lam = real(forgetting, "forgetting")
        if not 0 < lam <= 1:
            raise ValueError("forgetting must be in (0, 1]")
        dl = real(delta, "delta")
        if not dl > 0:
            raise ValueError("delta must be above 0")
        k_all = taps + m
        q_m = [[(1 / dl) + 0j if i == j else 0j for j in range(k_all)] for i in range(k_all)]
    s_p = 0j
    c_p = 0
    theta = nu = 0.0
    past = [0j] * m  # past[j - 1] is d_{n-j}
    out: list[complex] = []
    errors: list[complex] = []
    for n in range(n_out):
        base = n * sps + c
        u = [xs[base - i] if 0 <= base - i < len(xs) else 0j for i in range(taps)]
        v = 0j
        for wi, ui in zip(w, u, strict=True):
            v += wi * ui
        r = complex(math.cos(theta), -math.sin(theta))
        y = v * r if loop else v
        for bj, pj in zip(fb, past, strict=True):
            y += bj * pj
        out.append(y)
        pilot = k_p > 0 and n >= len(ts) and (n - len(ts)) % k_p == k_p - 1
        if n < len(ts):
            d: complex | None = ts[n]
        elif pilot:
            d = g_p[(n - len(ts)) // k_p]
        elif decision is not None:
            demap, mapper = _DECISIONS[decision]
            d = complex(mapper(demap(np.array([y])))[0])
        else:
            d = None
        if d is None:
            errors.append(0j)
            continue
        e = d - y
        errors.append(e)
        f = 0j
        for bj, pj in zip(fb, past, strict=True):
            f += bj * pj
        p = 0.0
        for ui in u:
            p += ui.real * ui.real + ui.imag * ui.imag
        for pj in past:
            p += pj.real * pj.real + pj.imag * pj.imag
        if p > 0 and q_m:
            z = [ui * r for ui in u] if loop else list(u)
            z += past
            qv = []
            for row in q_m:
                qi = 0j
                for qij, zj in zip(row, z, strict=True):
                    qi += qij * zj.conjugate()
                qv.append(qi)
            sv = complex(lam)
            for zi, qi in zip(z, qv, strict=True):
                sv += zi * qi
            gv = [qi / sv for qi in qv]
            w = [wi + gi * e for wi, gi in zip(w, gv[:taps], strict=True)]
            fb = [bj + gj * e for bj, gj in zip(fb, gv[taps:], strict=True)]
            tv = []
            for j in range(len(z)):
                tj = 0j
                for zi, row in zip(z, q_m, strict=True):
                    tj += zi * row[j]
                tv.append(tj)
            q_m = [
                [(qij - gi * tj) / lam for qij, tj in zip(row, tv, strict=True)]
                for row, gi in zip(q_m, gv, strict=True)
            ]
        elif p > 0:
            g = mu / p
            ef = e * r.conjugate() if loop else e
            w = [wi + g * ef * ui.conjugate() for wi, ui in zip(w, u, strict=True)]
            fb = [bj + g * e * pj.conjugate() for bj, pj in zip(fb, past, strict=True)]
        if loop:
            q = d - f
            cc = (v * r) * q.conjugate()
            ph = math.atan2(cc.imag, cc.real) if v != 0 and q != 0 else 0.0
            nu += loop[1] * ph
            theta += loop[0] * ph + nu
        if pilot:
            s_p += y * g_p[(n - len(ts)) // k_p].conjugate()
            c_p += 1
            if c_p == window:
                theta += round(math.atan2(s_p.imag, s_p.real) / sigma) * sigma
                s_p, c_p = 0j, 0
        if m:
            past = [d, *past[:-1]]
    return (
        np.array(out, dtype=np.complex128),
        np.array(errors, dtype=np.complex128),
        np.array(w, dtype=np.complex128),
        np.array(fb, dtype=np.complex128),
    )


def _start(values: ArrayLike, size: int, name: str) -> list[complex]:
    v = np.asarray(values)
    if v.ndim != 1 or v.size != size:
        raise ValueError(f"{name} must hold {size} values")
    v = np.asarray(v, dtype=np.complex128)
    if not np.all(np.isfinite(v)):
        raise ValueError(f"{name} must be finite")
    return [complex(z) for z in v.tolist()]


def _equalizer_args(
    samples: ArrayLike,
    training: ArrayLike,
    num_taps: int,
    num_feedback: int,
    samples_per_symbol: int,
    center: int | None,
) -> tuple[list[complex], list[complex], int, int, int, int]:
    x = np.asarray(samples)
    t = np.asarray(training)
    if x.ndim != 1 or t.ndim != 1:
        raise ValueError("samples and training must be one-dimensional")
    x = np.asarray(x, dtype=np.complex128)
    t = np.asarray(t, dtype=np.complex128)
    if x.size < 1:
        raise ValueError("samples needs at least 1")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(t))):
        raise ValueError("samples and training must be finite")
    taps = count(num_taps, "num_taps")
    sps = count(samples_per_symbol, "samples_per_symbol")
    if taps < 1 or sps < 1:
        raise ValueError("num_taps and samples_per_symbol must be at least 1")
    c = (taps - 1) // 2 if center is None else count(center, "center")
    if c >= taps:
        raise ValueError("center must be below num_taps")
    m = count(num_feedback, "num_feedback")
    n_out = -(-x.size // sps)
    if t.size > n_out:
        raise ValueError(f"training must be at most {n_out} symbols (the output count)")
    return x.tolist(), t.tolist(), taps, m, sps, c
