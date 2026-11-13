"""Convolution, upsampling, root-raised-cosine pulse shaping, FIR and IIR design and filtering.

Definitions are in docs/conventions.md (Pulse shaping, FIR filters, IIR filters),
docs/adr/0007-pulse-shaping-channel-evm.md, docs/adr/0010-fir-design-streaming.md and
docs/adr/0014-iir-filters.md.
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Callable
from typing import Any, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count, real
from .spectral import window as _window


def _vector(x: ArrayLike, what: str) -> NDArray[np.complex128] | NDArray[np.float64]:
    a = np.asarray(x)
    if a.ndim != 1 or a.size == 0:
        raise ValueError(f"{what} must be a non-empty 1-D array")
    if np.iscomplexobj(a):
        return np.asarray(a, dtype=np.complex128)
    return np.asarray(a, dtype=np.float64)


def convolve(x: ArrayLike, h: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Full linear convolution ``y[n] = sum h[k] x[n-k]``, length ``len(x) + len(h) - 1``."""
    y = np.convolve(_vector(x, "x"), _vector(h, "h"))
    return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def upsample(x: ArrayLike, factor: int) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Each sample followed by ``factor - 1`` zeros."""
    a = _vector(x, "x")
    if count(factor, "factor") < 1:
        raise ValueError("factor must be at least 1")
    y = np.zeros(a.size * factor, dtype=a.dtype)
    y[::factor] = a
    return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def rrc_taps(beta: float, samples_per_symbol: int, span_symbols: int) -> NDArray[np.float64]:
    """Root-raised-cosine taps, ``span * sps + 1`` of them, scaled to unit energy."""
    if not 0 <= beta <= 1:
        raise ValueError("beta must be in [0, 1]")
    sps = count(samples_per_symbol, "samples_per_symbol")
    span = count(span_symbols, "span_symbols")
    if sps < 1:
        raise ValueError("samples_per_symbol must be at least 1")
    if span < 2 or span % 2:
        raise ValueError("span_symbols must be even and at least 2")
    n = span * sps + 1
    h = np.empty(n)
    for i in range(n):
        t = (i - (n - 1) / 2) / sps
        if t == 0:
            h[i] = 1 - beta + 4 * beta / math.pi
        elif abs(4 * beta * abs(t) - 1) < 1e-9:
            a = math.pi / (4 * beta)
            h[i] = (
                beta
                / math.sqrt(2)
                * ((1 + 2 / math.pi) * math.sin(a) + (1 - 2 / math.pi) * math.cos(a))
            )
        else:
            num = math.sin(math.pi * t * (1 - beta)) + 4 * beta * t * math.cos(
                math.pi * t * (1 + beta)
            )
            h[i] = num / (math.pi * t * (1 - (4 * beta * t) ** 2))
    return np.asarray(h / math.sqrt(float(np.sum(h * h))), dtype=np.float64)


def pulse_shape(
    symbols: ArrayLike, taps: ArrayLike, samples_per_symbol: int
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``convolve(upsample(symbols, sps), taps)``; symbol ``k`` peaks at ``k*sps + (N-1)/2``."""
    return convolve(upsample(symbols, samples_per_symbol), taps)


def _fir_design(
    num_taps: int,
    ideal: list[tuple[float, float]],
    reference: float,
    window: str,
    beta: float | None,
) -> NDArray[np.float64]:
    """``sum sign * 2nu sinc(2nu t)`` over ``ideal`` (pairs ``(sign, nu)``), windowed, then scaled
    to unit zero-phase gain at the normalized ``reference`` frequency."""
    n = count(num_taps, "num_taps")
    if n < 1:
        raise ValueError("num_taps must be at least 1")
    t = np.arange(n, dtype=np.float64) - (n - 1) / 2
    d = np.zeros(n)
    for sign, nu in ideal:
        d += sign * 2 * nu * np.sinc(2 * nu * t)
    h = d * _window(window, n, symmetric=True, beta=beta)
    gain = float(np.sum(h * np.cos(2 * np.pi * reference * t)))
    if not abs(gain) > 1e-6 * float(np.sum(np.abs(h))):
        raise ValueError("too few taps: the design has almost no gain at its reference frequency")
    return np.asarray(h / gain, dtype=np.float64)


def _rate(sample_rate: float) -> float:
    fs = real(sample_rate, "sample_rate")
    if fs <= 0:
        raise ValueError("sample_rate must be positive")
    return fs


def _band_edge(f: float, fs: float, what: str) -> float:
    """``f/fs`` for a frequency strictly between 0 and ``fs/2``."""
    f = real(f, what)
    if not 0 < f < fs / 2:
        raise ValueError(f"{what} must be between 0 and sample_rate/2")
    return f / fs


def fir_lowpass(
    num_taps: int,
    cutoff: float,
    sample_rate: float,
    window: str = "hamming",
    beta: float | None = None,
) -> NDArray[np.float64]:
    """Windowed-sinc low-pass taps with unit gain at DC."""
    nu = _band_edge(cutoff, _rate(sample_rate), "cutoff")
    return _fir_design(num_taps, [(1.0, nu)], 0.0, window, beta)


def fir_highpass(
    num_taps: int,
    cutoff: float,
    sample_rate: float,
    window: str = "hamming",
    beta: float | None = None,
) -> NDArray[np.float64]:
    """Windowed-sinc high-pass taps with unit gain at ``sample_rate/2``; ``num_taps`` odd."""
    nu = _band_edge(cutoff, _rate(sample_rate), "cutoff")
    if count(num_taps, "num_taps") % 2 == 0:
        raise ValueError("a high-pass needs an odd num_taps")
    return _fir_design(num_taps, [(1.0, 0.5), (-1.0, nu)], 0.5, window, beta)


def fir_bandpass(
    num_taps: int,
    low: float,
    high: float,
    sample_rate: float,
    window: str = "hamming",
    beta: float | None = None,
) -> NDArray[np.float64]:
    """Windowed-sinc band-pass taps with unit gain at the band center ``(low + high)/2``."""
    fs = _rate(sample_rate)
    lo = _band_edge(low, fs, "low")
    hi = _band_edge(high, fs, "high")
    if lo >= hi:
        raise ValueError("low must be below high")
    return _fir_design(num_taps, [(1.0, hi), (-1.0, lo)], (lo + hi) / 2, window, beta)


def kaiser_parameters(
    attenuation_db: float, transition_width: float, sample_rate: float
) -> tuple[int, float]:
    """``(num_taps, beta)`` for a Kaiser-window design, from Kaiser's formulas (conventions)."""
    fs = _rate(sample_rate)
    a = real(attenuation_db, "attenuation_db")
    if a <= 0:
        raise ValueError("attenuation_db must be positive")
    dw = 2 * math.pi * _band_edge(transition_width, fs, "transition_width")
    if a > 50:
        beta = 0.1102 * (a - 8.7)
    elif a >= 21:
        beta = 0.5842 * (a - 21) ** 0.4 + 0.07886 * (a - 21)
    else:
        beta = 0.0
    order = max(0, math.ceil((a - 8) / (2.285 * dw)))
    if order >= 2**31 - 1:
        raise ValueError("transition_width is too narrow for any filter length")
    return order + 1, beta


EQUIRIPPLE_KINDS = ("filter", "hilbert", "differentiator")


def _equiripple_grid(
    num_taps: int,
    bands: ArrayLike,
    desired: ArrayLike,
    sample_rate: float,
    weights: ArrayLike | None,
    grid_density: int,
    kind: str,
) -> tuple[int, NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.int64]]:
    """Checked arguments as ``(L, nu, T, W, band index)`` on the grid (conventions): the target
    amplitude and the error weight at each point."""
    if kind not in EQUIRIPPLE_KINDS:
        raise ValueError(f"unknown kind {kind!r}; known: {', '.join(EQUIRIPPLE_KINDS)}")
    anti = kind != "filter"
    n = count(num_taps, "num_taps")
    if not (2 if anti else 1) <= n <= 1001:
        raise ValueError(f"num_taps must be in [{2 if anti else 1}, 1001] for kind {kind!r}")
    density = count(grid_density, "grid_density")
    if not 1 <= density <= 64:
        raise ValueError("grid_density must be in [1, 64]")
    fs = _rate(sample_rate)
    b = np.asarray(bands, dtype=np.float64)
    if b.ndim != 1 or b.size < 2 or b.size % 2 or not np.all(np.isfinite(b)):
        raise ValueError("bands must be a finite 1-D array of edge pairs")
    if b[0] < 0 or b[-1] > fs / 2 or np.any(np.diff(b) <= 0):
        raise ValueError("band edges must increase strictly from >= 0 to <= sample_rate/2")
    nb = b.size // 2
    d = np.asarray(desired, dtype=np.float64)
    if d.shape != (nb,) or not np.all(np.isfinite(d)):
        raise ValueError("desired must have one finite value per band")
    w = np.ones(nb) if weights is None else np.asarray(weights, dtype=np.float64)
    if w.shape != (nb,) or not np.all(np.isfinite(w)) or np.any(w <= 0):
        raise ValueError("weights must have one positive finite value per band")
    odd = n % 2 == 1
    # Q = 0 at 0.5 for types II and III, at 0 for III and IV: the target must be 0 there.
    if odd == anti and b[-1] == fs / 2 and d[-1] != 0:
        raise ValueError("num_taps and kind give zero gain at sample_rate/2: desired must be 0")
    if kind == "hilbert" and b[0] == 0 and d[0] != 0:
        raise ValueError("a Hilbert transformer has zero gain at 0: desired must be 0 there")
    big_l = (n - 1) // 2 if anti and odd else (n + 1) // 2 if odd else n // 2
    step = 0.5 / (density * big_l)
    nu: list[float] = []
    dd: list[float] = []
    ww: list[float] = []
    bi: list[int] = []
    for j in range(nb):
        lo, hi = b[2 * j] / fs, b[2 * j + 1] / fs
        m = math.ceil((hi - lo) / step)
        for i in range(m + 1):
            v = hi if i == m else lo + (hi - lo) * i / m
            if (v == 0.5 and odd == anti) or (v == 0 and anti):
                continue
            nu.append(v)
            if kind == "differentiator" and d[j] != 0:
                dd.append(-2 * math.pi * v * float(d[j]))
                ww.append(float(w[j]) / (2 * math.pi * v))
            else:
                dd.append(float(d[j]))
                ww.append(float(w[j]))
            bi.append(j)
    if len(nu) < big_l + 1:
        raise ValueError("the bands are too narrow for num_taps: too few grid points")
    return big_l, np.array(nu), np.array(dd), np.array(ww), np.array(bi, dtype=np.int64)


def _extrema(
    e: NDArray[np.float64], band: NDArray[np.int64], want: int, ext: NDArray[np.int64], s: float
) -> list[int]:
    """The new extremal set from the error on the grid (conventions: Equiripple design): the old
    set's points ``ext`` always count, with alternating signs starting at ``s``."""
    g = e.size
    sgn = np.sign(e)
    sgn[ext] = s * (-1.0) ** np.arange(ext.size)
    same_left = np.zeros(g, dtype=bool)
    same_left[1:] = band[1:] == band[:-1]
    same_right = np.zeros(g, dtype=bool)
    same_right[:-1] = band[:-1] == band[1:]
    left = np.concatenate(([0.0], e[:-1]))
    right = np.concatenate((e[1:], [0.0]))
    up = (e > 0) & (~same_left | (e >= left)) & (~same_right | (e >= right))
    down = (e < 0) & (~same_left | (e <= left)) & (~same_right | (e <= right))
    found = up | down
    found[ext] = True  # E = ±δ at the old set, so the new set always alternates L + 1 times
    mag = np.abs(e)

    def merge(ks: list[int]) -> list[int]:
        out: list[int] = []
        for k in ks:
            if out and sgn[k] == sgn[out[-1]]:
                if mag[k] > mag[out[-1]]:
                    out[-1] = k
            else:
                out.append(k)
        return out

    cand = merge([int(k) for k in np.flatnonzero(found)])
    while len(cand) > want:
        if len(cand) == want + 1:
            cand.pop(0 if mag[cand[0]] <= mag[cand[-1]] else -1)
        else:
            smallest = min(range(len(cand)), key=lambda i: mag[cand[i]])
            cand.pop(smallest)
            cand = merge(cand)
    return cand


def _barycentric(
    xs: NDArray[np.float64],
    nodes: NDArray[np.float64],
    bary: NDArray[np.float64],
    vals: NDArray[np.float64],
) -> NDArray[np.float64]:
    """The interpolant through ``(nodes, vals)`` at ``xs``, with barycentric weights ``bary``."""
    out = np.empty(xs.size)
    for s in range(0, xs.size, 1024):  # chunks keep the matrix to a few MB
        t = xs[s : s + 1024, None] - nodes[None, :]
        hit = t == 0
        t[hit] = 1.0
        r = bary / t
        with np.errstate(divide="ignore", invalid="ignore"):  # ±inf as in IEEE; caught later
            p = (r @ vals) / r.sum(axis=1)
        rows, cols = np.nonzero(hit)
        p[rows] = vals[cols]
        out[s : s + 1024] = p
    return out


def fir_equiripple(
    num_taps: int,
    bands: ArrayLike,
    desired: ArrayLike,
    sample_rate: float,
    weights: ArrayLike | None = None,
    grid_density: int = 16,
    kind: str = "filter",
) -> NDArray[np.float64]:
    """Parks-McClellan (Remez exchange) taps: the minimax weighted error over ``bands`` (edge pairs
    in Hz) with piecewise-constant ``desired`` values, on the conventions' grid. ``kind`` is
    ``"filter"`` (symmetric taps, ``desired`` gains), ``"hilbert"`` (antisymmetric, ``desired`` 1
    is the Hilbert transformer) or ``"differentiator"`` (antisymmetric, ``desired`` 1 is the
    derivative per sample, the error relative to it)."""
    _, _, dd, _, _ = _equiripple_grid(
        num_taps, bands, desired, sample_rate, weights, grid_density, kind
    )
    n = int(num_taps)
    if np.all(dd == 0) or (kind == "filter" and n % 2 == 1 and np.all(dd == dd[0])):
        h = np.zeros(n)
        h[(n - 1) // 2] = dd[0]  # exact: only reached for odd n unless every value is 0
        return h
    done = _remez(n, bands, desired, sample_rate, weights, grid_density, kind)
    if done is None:
        raise ValueError(
            "the equiripple design is beyond double precision: its ripple is too small, or its "
            "gaps between bands too wide, for double taps to reach"
        )
    return done[0]


def _antisymmetric_taps(c: NDArray[np.float64], odd: bool) -> NDArray[np.float64]:
    """Types III and IV: the taps from the cosine coefficients of ``P`` (conventions)."""
    big_l = c.size
    z = np.concatenate((c, [0.0, 0.0]))
    if odd:
        a = (z[:big_l] - z[2 : big_l + 2]) / 2  # a_m, m = 1 … L
        a[0] = c[0] - z[2] / 2
        return np.concatenate((-a[::-1] / 2, [0.0], a / 2))
    b = (z[:big_l] - z[1 : big_l + 1]) / 2  # b_m, m = 1 … L
    b[0] = c[0] - z[1] / 2
    return np.concatenate((-b[::-1] / 2, b / 2))


def _scaled_start(
    big_l: int, nu: NDArray[np.float64], band: NDArray[np.int64], prior: NDArray[np.float64] | None
) -> NDArray[np.int64]:
    """The first extremal set (conventions: Equiripple design, reference scaling) from the
    smaller design's final set ``prior`` (its frequencies), or by grid index without one."""
    g = nu.size
    if prior is None:
        return np.array([(i * (g - 1)) // big_l for i in range(big_l + 1)], dtype=np.int64)
    s = np.concatenate(([0.0], np.cumsum(np.where(band[1:] == band[:-1], np.diff(nu), 0.0))))
    sp = np.interp(prior, nu, s)
    lp = sp.size - 1
    t = np.interp(np.arange(big_l + 1) * lp / big_l, np.arange(lp + 1, dtype=np.float64), sp)
    idx = np.searchsorted(s, t)
    out = np.empty(big_l + 1, dtype=np.int64)
    for i, k in enumerate(idx):
        out[i] = max(int(k), out[i - 1] + 1) if i else int(k)
    return np.minimum(out, g - 1 - (big_l - np.arange(big_l + 1)))


def _remez(
    n: int,
    bands: ArrayLike,
    desired: ArrayLike,
    sample_rate: float,
    weights: ArrayLike | None,
    grid_density: int,
    kind: str,
) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
    """The exchange (conventions: Equiripple design): the taps and the final set's frequencies,
    or None if the design is beyond double precision."""
    big_l, nu, dd, ww, band = _equiripple_grid(
        n, bands, desired, sample_rate, weights, grid_density, kind
    )
    odd, anti = n % 2 == 1, kind != "filter"
    if anti:
        q = np.sin(2 * np.pi * nu) if odd else np.sin(np.pi * nu)
    else:
        q = np.ones_like(nu) if odd else np.cos(np.pi * nu)
    dp, wp, x = dd / q, ww * q, np.cos(2 * np.pi * nu)
    g = nu.size
    prior = None
    if big_l > 16:
        smaller = _remez(
            n - 2 * (big_l - (big_l + 1) // 2),
            bands,
            desired,
            sample_rate,
            weights,
            grid_density,
            kind,
        )
        prior = None if smaller is None else smaller[1]
    ext = _scaled_start(big_l, nu, band, prior)
    sign = (-1.0) ** np.arange(big_l + 1)
    slack = 1e-12 * float(np.max(np.abs(ww * dd)))
    for _ in range(250):
        xe = x[ext]
        diff = xe[:, None] - xe[None, :]
        np.fill_diagonal(diff, 1.0)
        logs = np.sum(np.log(np.abs(diff)), axis=1)
        gamma = np.prod(np.sign(diff), axis=1) * np.exp(logs.min() - logs)
        delta = float(np.dot(gamma, dp[ext]) / np.dot(gamma * sign, 1 / wp[ext]))
        values = dp[ext] - sign * delta / wp[ext]
        nodes, vals = xe[:big_l], values[:big_l]
        bary = gamma[:big_l] * (nodes - xe[big_l])

        e = wp * (dp - _barycentric(x, nodes, bary, vals))
        e[ext] = sign * delta  # exact at the set; the last point is not a node
        new = _extrema(e, band, big_l + 1, ext, 1.0 if delta >= 0 else -1.0)
        if len(new) < big_l + 1:
            break
        if np.array_equal(new, ext) or np.max(np.abs(e)) <= abs(delta) * (1 + 1e-9) + slack:
            # The cosine coefficients by a direct solve at the set: sampling P across the gaps
            # between bands would amplify rounding there (the interpolant is ill-conditioned).
            k = np.arange(big_l)
            a = np.empty((big_l + 1, big_l + 1))
            a[:, :big_l] = np.cos(2 * np.pi * np.outer(nu[ext], k))
            a[:, big_l] = sign / wp[ext]
            c = np.linalg.solve(a, dp[ext])[:big_l]
            worst = 0.0
            for s in range(0, g, 1024):
                p = np.cos(2 * np.pi * np.outer(nu[s : s + 1024], k)) @ c
                worst = max(worst, float(np.max(np.abs(wp[s : s + 1024] * (dp[s : s + 1024] - p)))))
            if worst > abs(delta) * (1 + 1e-3) + 100 * slack:
                break
            if anti:
                return _antisymmetric_taps(c, odd), nu[ext]
            if odd:
                return np.concatenate((c[:0:-1] / 2, c[:1], c[1:] / 2)), nu[ext]
            beta = np.empty(big_l)
            beta[0] = c[0] + (c[1] / 2 if big_l > 1 else 0.0)
            if big_l > 1:
                beta[1:-1] = (c[1:-1] + c[2:]) / 2
                beta[-1] = c[-1] / 2
            return np.concatenate((beta[::-1] / 2, beta / 2)), nu[ext]
        ext = np.array(new)
    return None


def _taps(taps: ArrayLike) -> NDArray[np.float64]:
    h = np.asarray(taps)
    if h.ndim != 1 or h.size == 0 or np.iscomplexobj(h):
        raise ValueError("taps must be a non-empty 1-D real array")
    h = np.array(h, dtype=np.float64)  # a copy: callers may change theirs
    if not np.all(np.isfinite(h)):
        raise ValueError("taps must be finite")
    return h


def fir_least_squares(
    num_taps: int,
    bands: ArrayLike,
    desired: ArrayLike,
    sample_rate: float,
    weights: ArrayLike | None = None,
) -> NDArray[np.float64]:
    """Symmetric taps minimizing the weighted integral squared error over ``bands`` (edge pairs in
    Hz), the desired gain linear across each band from its two ``desired`` edge values
    (conventions: FIR filters, Least-squares design)."""
    n = count(num_taps, "num_taps")
    if not 1 <= n <= 1001:
        raise ValueError("num_taps must be in [1, 1001]")
    fs = _rate(sample_rate)
    b = np.asarray(bands, dtype=np.float64)
    if b.ndim != 1 or b.size < 2 or b.size % 2 or not np.all(np.isfinite(b)):
        raise ValueError("bands must be a finite 1-D array of edge pairs")
    if b[0] < 0 or b[-1] > fs / 2 or np.any(np.diff(b) <= 0):
        raise ValueError("band edges must increase strictly from >= 0 to <= sample_rate/2")
    nb = b.size // 2
    d = np.asarray(desired, dtype=np.float64)
    if d.shape != (2 * nb,) or not np.all(np.isfinite(d)):
        raise ValueError("desired must have two finite values per band (its edge gains)")
    w = np.ones(nb) if weights is None else np.asarray(weights, dtype=np.float64)
    if w.shape != (nb,) or not np.all(np.isfinite(w)) or np.any(w <= 0):
        raise ValueError("weights must have one positive finite value per band")
    odd = n % 2 == 1
    big_l = (n + 1) // 2 if odd else n // 2
    t = np.arange(big_l, dtype=np.float64) + (0.0 if odd else 0.5)
    diff = t[:, None] - t[None, :]
    summ = t[:, None] + t[None, :]
    g = np.zeros((big_l, big_l))
    p = np.zeros(big_l)
    for j in range(nb):
        lo, hi = b[2 * j] / fs, b[2 * j + 1] / fs
        slope = (d[2 * j + 1] - d[2 * j]) / (hi - lo)
        g += w[j] * (_cos_integral(diff, lo, hi) + _cos_integral(summ, lo, hi)) / 2
        level = d[2 * j] - slope * lo  # D(nu) = level + slope * nu
        p += w[j] * (level * _cos_integral(t, lo, hi) + slope * _nu_cos_integral(t, lo, hi))
    a = np.linalg.solve(g, p)
    h = np.zeros(n)
    if odd:
        c = (n - 1) // 2
        h[c] = a[0]
        h[c + 1 :] = a[1:] / 2
        h[:c] = a[:0:-1] / 2
    else:
        h[n // 2 :] = a / 2
        h[: n // 2] = a[::-1] / 2
    return h


def _cos_integral(u: NDArray[np.float64], lo: float, hi: float) -> NDArray[np.float64]:
    """``C(u)``: the integral of ``cos(2 pi u nu)`` over ``[lo, hi]`` (conventions)."""
    k = 2 * np.pi * np.where(u == 0, 1.0, u)
    out = (np.sin(k * hi) - np.sin(k * lo)) / k
    return np.asarray(np.where(u == 0, hi - lo, out), dtype=np.float64)


def _nu_cos_integral(u: NDArray[np.float64], lo: float, hi: float) -> NDArray[np.float64]:
    """``S(u)``: the integral of ``nu cos(2 pi u nu)`` over ``[lo, hi]`` (conventions)."""
    k = 2 * np.pi * np.where(u == 0, 1.0, u)

    def f(v: float) -> NDArray[np.float64]:
        return np.asarray(v * np.sin(k * v) / k + np.cos(k * v) / k**2, dtype=np.float64)

    return np.asarray(np.where(u == 0, (hi * hi - lo * lo) / 2, f(hi) - f(lo)), dtype=np.float64)


def fir_response(
    taps: ArrayLike, frequencies: ArrayLike, sample_rate: float
) -> NDArray[np.complex128]:
    """Complex response ``H(f) = sum h[n] exp(-j 2 pi f n / fs)`` at each frequency."""
    h = _taps(taps)
    fs = _rate(sample_rate)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.ndim != 1 or not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be a finite 1-D array")
    n = np.arange(h.size, dtype=np.float64)
    return np.asarray(np.exp(-2j * np.pi * np.outer(f / fs, n)) @ h, dtype=np.complex128)


def fir_group_delay(
    taps: ArrayLike, frequencies: ArrayLike, sample_rate: float
) -> NDArray[np.float64]:
    """Group delay ``-d(phase)/d(omega)`` in samples at each frequency, in closed form; NaN where
    the response is within rounding of 0 (conventions: FIR filters, Group delay)."""
    h = _taps(taps)
    fs = _rate(sample_rate)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.ndim != 1 or not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be a finite 1-D array")
    return _poly_delay(h, f / fs)


def _poly_delay(c: NDArray[np.float64], nu: NDArray[np.float64]) -> NDArray[np.float64]:
    """``Re(R/P)`` for ``P = sum c_n e^(-j 2 pi nu n)``, ``R = sum n c_n e^(-j 2 pi nu n)``; NaN
    where ``|P| <= 1e-10 sum |c_n|``."""
    n = np.arange(c.size, dtype=np.float64)
    e = np.exp(-2j * np.pi * np.outer(nu, n))
    p = e @ c
    r = e @ (n * c)
    small = np.abs(p) <= 1e-10 * np.sum(np.abs(c))
    tau = np.real(r / np.where(small, 1.0, p))
    return np.asarray(np.where(small, np.nan, tau), dtype=np.float64)


class FirFilter:
    """Causal direct-form FIR filter that keeps its state across chunks (conventions: FIR filters).

    The first non-empty chunk fixes the filter as real or complex until :meth:`reset`.
    """

    def __init__(self, taps: ArrayLike) -> None:
        self._h = _taps(taps)
        self._complex: bool | None = None
        self._state: NDArray[np.complex128] | NDArray[np.float64] = np.zeros(0)

    @property
    def taps(self) -> NDArray[np.float64]:
        """A copy of the taps."""
        return self._h.copy()

    def reset(self) -> None:
        """Forget every sample seen, as if new."""
        self._complex = None
        self._state = np.zeros(0)

    def process(self, chunk: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
        """The next ``len(chunk)`` output samples."""
        a = np.asarray(chunk)
        if a.ndim != 1:
            raise ValueError("chunk must be a 1-D array")
        is_complex = bool(np.iscomplexobj(a))
        x = np.asarray(a, dtype=np.complex128 if is_complex else np.float64)
        if x.size == 0:
            empty = np.zeros(0, dtype=np.complex128 if self._complex else np.float64)
            return cast("NDArray[np.complex128] | NDArray[np.float64]", empty)
        if self._complex is None:
            self._complex = is_complex
            self._state = cast(
                "NDArray[np.complex128] | NDArray[np.float64]",
                np.zeros(self._h.size - 1, dtype=x.dtype),
            )
        elif self._complex != is_complex:
            kind = "complex" if self._complex else "real"
            raise ValueError(f"this filter takes {kind} samples until reset()")
        ext = np.concatenate([self._state, x])
        y = np.convolve(ext, self._h, mode="valid")
        self._state = ext[ext.size - (self._h.size - 1) :]
        return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def _sos(sos: ArrayLike) -> NDArray[np.float64]:
    """A copy of a cascade of second-order sections, each row divided by its ``a0``."""
    s = np.asarray(sos)
    if s.ndim != 2 or s.shape[0] == 0 or s.shape[1] != 6 or np.iscomplexobj(s):
        raise ValueError(
            "sos must be a real array of shape (sections, 6) with at least one section"
        )
    s = np.array(s, dtype=np.float64)
    if not np.all(np.isfinite(s)):
        raise ValueError("sos must be finite")
    if np.any(s[:, 3] == 0):
        raise ValueError("every section needs a0 != 0")
    return np.asarray(s / s[:, 3:4], dtype=np.float64)


def _order(order: int) -> int:
    n = count(order, "order")
    if not 1 <= n <= 1000:
        raise ValueError("order must be between 1 and 1000")
    return n


def _usable(rows: list[list[float]]) -> NDArray[np.float64]:
    """The design's sections, if each is finite and strictly stable; a cutoff (or band edge) too
    near 0 or fs/2 rounds to a pole on the unit circle and is rejected."""
    for row in rows:
        a1, a2 = row[4], row[5]
        if not (all(math.isfinite(v) for v in row) and abs(a2) < 1 and abs(a1) < 1 + a2):
            raise ValueError(
                "the design rounds to a pole on or outside the unit circle: the cutoff is too "
                "close to 0 or sample_rate/2 (or the dB value too small) for double precision"
            )
    return np.array(rows, dtype=np.float64)


def _db_power_ratio(x: float, name: str) -> float:
    """``10^(x/10) - 1`` for ``0 < x <= 200`` dB, without losing digits for small ``x``."""
    v = real(x, name)
    if not 0 < v <= 200:
        raise ValueError(f"{name} must be in (0, 200] dB")
    return math.expm1(v * math.log(10) / 10)


def _theta(i: int, n: int) -> float:
    return math.pi / 2 + math.pi * (2 * i + 1) / (2 * n)


def _butterworth(order: int, cutoff: float, sample_rate: float, high: bool) -> NDArray[np.float64]:
    n = _order(order)
    return _cascade(n, cutoff, sample_rate, high, lambda i: cmath.exp(1j * _theta(i, n)))


def _bessel_theta(n: int, s: complex) -> tuple[complex, complex]:
    """The reverse Bessel polynomial and its derivative at ``s``, by the recurrence."""
    t0, t1, d0, d1 = 1 + 0j, s + 1, 0j, 1 + 0j
    for k in range(2, n + 1):
        t0, t1, d0, d1 = (
            t1,
            (2 * k - 1) * t1 + s * s * t0,
            d1,
            (2 * k - 1) * d1 + 2 * s * t0 + s * s * d0,
        )
    return t1, d1


def _bessel_prototype(n: int) -> list[complex]:
    """The Bessel prototype's poles normalized to -3 dB at 1 (conventions: Bessel design): pair
    ``i``'s upper pole for ``i < n // 2``, from the highest Q, then the real pole for an odd
    ``n``."""
    a0 = math.factorial(2 * n) / (2**n * math.factorial(n))
    r = a0 ** (1 / n)  # the roots' geometric mean; Aberth starts on Butterworth's angles
    z = [r * cmath.exp(1j * _theta(i, n)) for i in range(n)]
    for _ in range(100):
        steps = []
        for i, zi in enumerate(z):
            t, dt = _bessel_theta(n, zi)
            w = t / dt
            steps.append(w / (1 - w * sum(1 / (zi - zj) for j, zj in enumerate(z) if j != i)))
        z = [zi - st for zi, st in zip(z, steps, strict=True)]
        if max(abs(st) / abs(zi) for zi, st in zip(z, steps, strict=True)) <= 1e-15:
            break
    z = [zi - _bessel_theta(n, zi)[0] / _bessel_theta(n, zi)[1] for zi in z]  # a Newton step
    lo, hi = 0.0, 1.0  # omega_0: |theta(j w)|^2 = 2 theta(0)^2, increasing in w
    while abs(_bessel_theta(n, 1j * hi)[0]) ** 2 < 2 * a0 * a0:
        hi *= 2
    while lo < (mid := (lo + hi) / 2) < hi:
        if abs(_bessel_theta(n, 1j * mid)[0]) ** 2 < 2 * a0 * a0:
            lo = mid
        else:
            hi = mid
    w0 = (lo + hi) / 2
    real = [p for p in z if abs(p.imag) <= 1e-12 * abs(p)]  # the real pole: zero to rounding
    pairs = sorted((p for p in z if p.imag > 1e-12 * abs(p)), key=lambda p: -p.imag / -p.real)
    return [p / w0 for p in pairs] + [complex(p.real / w0, 0) for p in real]


def _bessel_poles(order: int) -> list[complex]:
    n = count(order, "order")
    if not 1 <= n <= 10:
        raise ValueError("order must be between 1 and 10: higher Bessel poles are lost to rounding")
    return _bessel_prototype(n)


def _bessel(order: int, cutoff: float, sample_rate: float, high: bool) -> NDArray[np.float64]:
    poles = _bessel_poles(order)
    return _cascade(int(order), cutoff, sample_rate, high, lambda i: poles[i])


def _bessel_band(
    order: int, low: float, high: float, sample_rate: float, stop: bool
) -> NDArray[np.float64]:
    poles = _bessel_poles(order)
    return _band(int(order), low, high, sample_rate, stop, lambda i: poles[i])


def _chebyshev1(
    order: int, ripple_db: float, cutoff: float, sample_rate: float, high: bool
) -> NDArray[np.float64]:
    n = _order(order)
    eps2 = _db_power_ratio(ripple_db, "ripple_db")
    r = float(ripple_db)
    mu = math.asinh(1 / math.sqrt(eps2)) / n
    sh, ch = math.sinh(mu), math.cosh(mu)
    rows = _cascade(
        n,
        cutoff,
        sample_rate,
        high,
        lambda i: complex(sh * math.cos(_theta(i, n)), ch * math.sin(_theta(i, n))),
    )
    if n % 2 == 0:
        rows[0, :3] *= 10 ** (-r / 20)  # the ripple's low point at DC (or fs/2)
    return rows


def _chebyshev2(
    order: int, attenuation_db: float, cutoff: float, sample_rate: float, high: bool
) -> NDArray[np.float64]:
    n = _order(order)
    mu = math.asinh(math.sqrt(_db_power_ratio(attenuation_db, "attenuation_db"))) / n
    sh, ch = math.sinh(mu), math.cosh(mu)
    return _cascade(
        n,
        cutoff,
        sample_rate,
        high,
        lambda i: 1 / complex(sh * math.cos(_theta(i, n)), ch * math.sin(_theta(i, n))),
        lambda i: 1 / math.sin(_theta(i, n)),
    )


def _landen(m: float, mp: float) -> list[float]:
    """Descending Landen moduli ``m_1, m_2, ...`` of ``m`` (complement ``mp`` given separately)."""
    out = []
    while m > 1e-12:
        m, mp = (m / (1 + mp)) ** 2, 2 * math.sqrt(mp) / (1 + mp)
        out.append(m)
    return out


def _ellip_k(m: float, mp: float) -> float:
    """Complete elliptic integral of the first kind ``K(m)``."""
    return math.pi / 2 * math.prod(1 + v for v in _landen(m, mp))


def _cd(u: complex, ladder: list[float]) -> complex:
    """Jacobi ``cd(u K, m)`` from ``m``'s Landen ladder."""
    w = cmath.cos(u * math.pi / 2)
    for v in reversed(ladder):
        w = (1 + v) * w / (1 + v * w * w)
    return w


def _selectivity(n: int, k1: float, k1p: float) -> tuple[float, float]:
    """``k`` and ``k'`` from the degree equation ``K'(k)/K(k) = K'(k1)/(n K(k1))``."""
    tau = _ellip_k(k1p, k1) / (n * _ellip_k(k1, k1p))

    def product(q: float) -> float:
        p, m = 4 * math.sqrt(q), 1
        while q ** (2 * m - 1) > 1e-18:
            p *= ((1 + q ** (2 * m)) / (1 + q ** (2 * m - 1))) ** 4
            m += 1
        return p

    if tau >= 1:
        k = product(math.exp(-math.pi * tau))
        return k, math.sqrt((1 - k) * (1 + k))
    kp = product(math.exp(-math.pi / tau))
    return math.sqrt((1 - kp) * (1 + kp)), kp


def _elliptic_prototype(
    n: int, ripple_db: float, attenuation_db: float
) -> tuple[Callable[[int], complex], Callable[[int], float]]:
    """The elliptic prototype's pole ``i`` and pair ``i``'s zero frequency (edge 1)."""
    ep = math.sqrt(_db_power_ratio(ripple_db, "ripple_db"))
    es = math.sqrt(_db_power_ratio(attenuation_db, "attenuation_db"))
    if not float(ripple_db) < float(attenuation_db):
        raise ValueError("ripple_db must be less than attenuation_db")
    k1 = ep / es
    k1p = math.sqrt((1 - k1) * (1 + k1))
    k, kp = _selectivity(n, k1, k1p)
    if not kp >= 1e-6:  # the stop band would start within k'^2/2 (5e-13) of the cutoff
        raise ValueError(
            "the transition band is too narrow for double precision (k' < 1e-6): the order is "
            "too high for ripple_db and attenuation_db"
        )
    y, prev = 1 / ep, k1
    for v in _landen(k1, k1p):
        y = 2 * y / ((1 + v) * (1 + math.sqrt(1 + prev * prev * y * y)))
        prev = v
    v0 = 2 / math.pi * math.asinh(y) / n
    ladder = _landen(k, kp)
    return (
        lambda i: 1j * _cd((2 * i + 1) / n - 1j * v0, ladder),
        lambda i: 1 / (k * _cd((2 * i + 1) / n, ladder).real),
    )


def _elliptic(
    order: int,
    ripple_db: float,
    attenuation_db: float,
    cutoff: float,
    sample_rate: float,
    high: bool,
) -> NDArray[np.float64]:
    n = _order(order)
    poles, zeros = _elliptic_prototype(n, ripple_db, attenuation_db)
    rows = _cascade(n, cutoff, sample_rate, high, poles, zeros)
    if n % 2 == 0:
        rows[0, :3] *= 10 ** (-float(ripple_db) / 20)  # the ripple's low point at DC (or fs/2)
    return rows


def _cascade(
    n: int,
    cutoff: float,
    sample_rate: float,
    high: bool,
    prototype: Callable[[int], complex],
    zeros: Callable[[int], float] | None = None,
) -> NDArray[np.float64]:
    """Sections from the analog prototype poles (cutoff 1) and, for pair ``i``, zeros at
    ``s = ±j·zeros(i)`` (default: Butterworth's, at infinity): low-pass or high-pass, prewarped
    bilinear transform, Butterworth section order and unit gain at DC or fs/2."""
    fs = _rate(sample_rate)
    k = math.tan(math.pi * _band_edge(cutoff, fs, "cutoff"))
    zero = 1.0 if high else -1.0  # zeros at z = 1 (high-pass) or z = -1 (low-pass)
    rows: list[list[float]] = []

    def pole(i: int) -> complex:
        """Prototype pole ``i`` scaled to the prewarped cutoff, through the bilinear transform."""
        s = k / prototype(i) if high else k * prototype(i)
        return (1 + s) / (1 - s)

    if n % 2:
        p = pole((n - 1) // 2).real
        g = (1 + p) / 2 if high else (1 - p) / 2  # unit gain at fs/2 or DC
        rows.append([g, -zero * g, 0.0, 1.0, -p, 0.0])
    for i in range(n // 2 - 1, -1, -1):
        z = pole(i)
        a1, a2 = -2 * z.real, abs(z) ** 2
        c, ref = zero, 4.0  # numerator 1 - 2c z^-1 + z^-2: a double zero at z = zero, or a pair
        if zeros is not None:  # on the circle; ref = 2 + 2 zero c, its value at z = -zero, exactly
            w = k / zeros(i) if high else k * zeros(i)
            c = (1 - w * w) / (1 + w * w)
            ref = 4 / (1 + w * w) if high else 4 * w * w / (1 + w * w)
        g = (1 - zero * a1 + a2) / ref  # unit gain at the reference z = -zero
        rows.append([g, -2 * c * g, g, 1.0, a1, a2])
    return _usable(rows)


def butterworth_lowpass(order: int, cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """Butterworth low-pass by the bilinear transform, as second-order sections (conventions: IIR
    filters)."""
    return _butterworth(order, cutoff, sample_rate, high=False)


def butterworth_highpass(order: int, cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """Butterworth high-pass by the bilinear transform, as second-order sections (conventions: IIR
    filters)."""
    return _butterworth(order, cutoff, sample_rate, high=True)


def bessel_lowpass(order: int, cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """Bessel (maximally flat delay) low-pass by the bilinear transform, as second-order sections,
    -3 dB at ``cutoff`` (conventions: IIR filters)."""
    return _bessel(order, cutoff, sample_rate, high=False)


def bessel_highpass(order: int, cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """Bessel high-pass by the bilinear transform, as second-order sections, -3 dB at ``cutoff``
    (conventions: IIR filters)."""
    return _bessel(order, cutoff, sample_rate, high=True)


def chebyshev1_lowpass(
    order: int, ripple_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type I low-pass by the bilinear transform, as second-order sections: pass-band
    ripple ``ripple_db``, which ``cutoff`` ends (conventions: IIR filters)."""
    return _chebyshev1(order, ripple_db, cutoff, sample_rate, high=False)


def chebyshev1_highpass(
    order: int, ripple_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type I high-pass by the bilinear transform, as second-order sections: pass-band
    ripple ``ripple_db``, which starts at ``cutoff`` (conventions: IIR filters)."""
    return _chebyshev1(order, ripple_db, cutoff, sample_rate, high=True)


def chebyshev2_lowpass(
    order: int, attenuation_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type II low-pass by the bilinear transform, as second-order sections: flat pass
    band, stop band from ``cutoff`` with peaks at ``-attenuation_db`` (conventions: IIR filters)."""
    return _chebyshev2(order, attenuation_db, cutoff, sample_rate, high=False)


def chebyshev2_highpass(
    order: int, attenuation_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type II high-pass by the bilinear transform, as second-order sections: flat pass
    band, stop band up to ``cutoff`` with peaks at ``-attenuation_db`` (conventions: IIR
    filters)."""
    return _chebyshev2(order, attenuation_db, cutoff, sample_rate, high=True)


def elliptic_lowpass(
    order: int, ripple_db: float, attenuation_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Elliptic (Cauer) low-pass by the bilinear transform, as second-order sections: pass-band
    ripple ``ripple_db``, which ``cutoff`` ends, and stop-band peaks at ``-attenuation_db``
    (conventions: IIR filters)."""
    return _elliptic(order, ripple_db, attenuation_db, cutoff, sample_rate, high=False)


def elliptic_highpass(
    order: int, ripple_db: float, attenuation_db: float, cutoff: float, sample_rate: float
) -> NDArray[np.float64]:
    """Elliptic (Cauer) high-pass by the bilinear transform, as second-order sections: pass-band
    ripple ``ripple_db`` from ``cutoff``, and stop-band peaks at ``-attenuation_db`` (conventions:
    IIR filters)."""
    return _elliptic(order, ripple_db, attenuation_db, cutoff, sample_rate, high=True)


def _butterworth_band(
    order: int, low: float, high: float, sample_rate: float, stop: bool
) -> NDArray[np.float64]:
    n = _order(order)
    poles = lambda i: cmath.exp(1j * _theta(i, n))  # noqa: E731
    return _band(n, low, high, sample_rate, stop, poles, unit=True)


def _chebyshev_poles(n: int, db: float, name: str, inverse: bool) -> Callable[[int], complex]:
    """Type I prototype poles for ripple ``db`` (``inverse``: type II, their reciprocals, for
    attenuation ``db``)."""
    eps2 = _db_power_ratio(db, name)
    mu = math.asinh(math.sqrt(eps2) if inverse else 1 / math.sqrt(eps2)) / n
    sh, ch = math.sinh(mu), math.cosh(mu)

    def pole(i: int) -> complex:
        p = complex(sh * math.cos(_theta(i, n)), ch * math.sin(_theta(i, n)))
        return 1 / p if inverse else p

    return pole


def _chebyshev1_band(
    order: int, ripple_db: float, low: float, high: float, sample_rate: float, stop: bool
) -> NDArray[np.float64]:
    n = _order(order)
    poles = _chebyshev_poles(n, ripple_db, "ripple_db", False)
    rows = _band(n, low, high, sample_rate, stop, poles)
    if n % 2 == 0:
        rows[0, :3] *= 10 ** (-float(ripple_db) / 20)  # the ripple's low point at the reference
    return rows


def _chebyshev2_band(
    order: int, attenuation_db: float, low: float, high: float, sample_rate: float, stop: bool
) -> NDArray[np.float64]:
    n = _order(order)
    poles = _chebyshev_poles(n, attenuation_db, "attenuation_db", True)
    return _band(n, low, high, sample_rate, stop, poles, lambda i: 1 / math.sin(_theta(i, n)))


def _elliptic_band(
    order: int,
    ripple_db: float,
    attenuation_db: float,
    low: float,
    high: float,
    sample_rate: float,
    stop: bool,
) -> NDArray[np.float64]:
    n = _order(order)
    poles, zeros = _elliptic_prototype(n, ripple_db, attenuation_db)
    rows = _band(n, low, high, sample_rate, stop, poles, zeros)
    if n % 2 == 0:
        rows[0, :3] *= 10 ** (-float(ripple_db) / 20)  # the ripple's low point at the reference
    return rows


def _band(
    n: int,
    low: float,
    high: float,
    sample_rate: float,
    stop: bool,
    prototype: Callable[[int], complex],
    zeros: Callable[[int], float] | None = None,
    unit: bool = False,
) -> NDArray[np.float64]:
    """Band-pass or band-stop sections from the low-pass prototype's poles (edge 1) and, for pair
    ``i``, zeros at ``s = ±j·zeros(i)`` (default: at infinity), with the prototype's gain
    (``unit``: the poles are on the unit circle, so the pair gains are exactly 1)."""
    fs = _rate(sample_rate)
    lo = math.tan(math.pi * _band_edge(low, fs, "low"))
    hi = math.tan(math.pi * _band_edge(high, fs, "high"))
    if lo >= hi:
        raise ValueError("low must be below high")
    w2, bw = lo * hi, hi - lo  # center squared and width, prewarped
    rows: list[list[float]] = []

    def section(sigma: float, m: float, gain: float, zero2: float | None) -> None:
        """Analog section with poles at ``s`` and its conjugate (``sigma = Re s``, ``m = |s|^2``)
        times ``gain``, through the bilinear transform ``s = (1 - z^-1)/(1 + z^-1)``, divided by
        ``a0``; numerator ``s^2 + zero2`` if given, else as for Butterworth."""
        a0 = 1 - 2 * sigma + m
        if zero2 is not None:  # (s^2 + zero2) / ...
            b = [1 + zero2, 2 * (zero2 - 1), 1 + zero2]
        elif stop:  # (s^2 + w2) / ...
            b = [1 + w2, 2 * (w2 - 1), 1 + w2]
        else:  # bw * s / ...
            b = [bw, 0.0, -bw]
        rows.append([*(gain * v / a0 for v in b), 1.0, 2 * (m - 1) / a0, (1 + 2 * sigma + m) / a0])

    if n % 2:  # the real pole p maps to s^2 - c*s + w2, one section whatever its roots
        pr = prototype((n - 1) // 2).real
        cr = bw / pr if stop else bw * pr
        section(cr / 2, w2, 1.0 if stop else -pr, None)
    for i in range(n // 2 - 1, -1, -1):
        p = prototype(i)
        c = bw / p if stop else bw * p  # the pole's two images: roots of s^2 - c*s + w2
        r = cmath.sqrt(c * c - 4 * w2)
        images = sorted([(c + r) / 2, (c - r) / 2], key=abs)
        zero2: list[float | None] = [None, None]
        if zeros is None:
            gain = 1.0 if stop or unit else abs(p)
        else:  # j*omega maps to j*w_hi and j*w_lo, w_hi * w_lo = w2
            d = bw / zeros(i) if stop else bw * zeros(i)
            w_hi = (d + math.sqrt(d * d + 4 * w2)) / 2
            gain = 1.0 if stop else abs(p) / zeros(i)
            zero2 = [(w2 / w_hi) ** 2, w_hi * w_hi]
        for s, z2 in zip(images, zero2, strict=True):
            section(s.real, abs(s) ** 2, gain, z2)
    return _usable(rows)


def bessel_bandpass(order: int, low: float, high: float, sample_rate: float) -> NDArray[np.float64]:
    """Bessel band-pass from the low-pass prototype of that order, by the bilinear transform, as
    ``order`` second-order sections, -3 dB at ``low`` and ``high`` (conventions: IIR filters)."""
    return _bessel_band(order, low, high, sample_rate, stop=False)


def bessel_bandstop(order: int, low: float, high: float, sample_rate: float) -> NDArray[np.float64]:
    """Bessel band-stop from the low-pass prototype of that order, by the bilinear transform, as
    ``order`` second-order sections, -3 dB at ``low`` and ``high`` (conventions: IIR filters)."""
    return _bessel_band(order, low, high, sample_rate, stop=True)


def _allpass_c(f: float, fs: float, what: str) -> float:
    t = math.tan(math.pi * _band_edge(f, fs, what))
    return (t - 1) / (t + 1)


def allpass_first_order(cutoff: float, sample_rate: float) -> NDArray[np.float64]:
    """First-order all-pass section, phase -pi/2 at ``cutoff`` (conventions: IIR filters,
    All-pass sections)."""
    c = _allpass_c(cutoff, _rate(sample_rate), "cutoff")
    return _usable([[c, 1.0, 0.0, 1.0, c, 0.0]])


def allpass_second_order(
    center: float, bandwidth: float, sample_rate: float
) -> NDArray[np.float64]:
    """Second-order all-pass section, phase -pi at ``center`` and -pi/2, -3pi/2 at two frequencies
    ``bandwidth`` apart (conventions: IIR filters, All-pass sections)."""
    fs = _rate(sample_rate)
    d = -math.cos(2 * math.pi * _band_edge(center, fs, "center"))
    c = _allpass_c(bandwidth, fs, "bandwidth")
    return _usable([[-c, d * (1 - c), 1.0, 1.0, d * (1 - c), -c]])


def butterworth_bandpass(
    order: int, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Butterworth band-pass from the low-pass prototype of that order, by the bilinear transform,
    as ``order`` second-order sections (conventions: IIR filters)."""
    return _butterworth_band(order, low, high, sample_rate, stop=False)


def butterworth_bandstop(
    order: int, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Butterworth band-stop from the low-pass prototype of that order, by the bilinear transform,
    as ``order`` second-order sections (conventions: IIR filters)."""
    return _butterworth_band(order, low, high, sample_rate, stop=True)


def chebyshev1_bandpass(
    order: int, ripple_db: float, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type I band-pass from the low-pass prototype of that order: pass band
    ``[low, high]`` rippling by ``ripple_db``, ``order`` second-order sections (conventions: IIR
    filters)."""
    return _chebyshev1_band(order, ripple_db, low, high, sample_rate, stop=False)


def chebyshev1_bandstop(
    order: int, ripple_db: float, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type I band-stop from the low-pass prototype of that order: pass bands up to
    ``low`` and from ``high``, rippling by ``ripple_db``, ``order`` second-order sections
    (conventions: IIR filters)."""
    return _chebyshev1_band(order, ripple_db, low, high, sample_rate, stop=True)


def chebyshev2_bandpass(
    order: int, attenuation_db: float, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type II band-pass from the low-pass prototype of that order: stop bands up to
    ``low`` and from ``high`` with peaks at ``-attenuation_db``, ``order`` second-order sections
    (conventions: IIR filters)."""
    return _chebyshev2_band(order, attenuation_db, low, high, sample_rate, stop=False)


def chebyshev2_bandstop(
    order: int, attenuation_db: float, low: float, high: float, sample_rate: float
) -> NDArray[np.float64]:
    """Chebyshev type II band-stop from the low-pass prototype of that order: stop band
    ``[low, high]`` with peaks at ``-attenuation_db``, ``order`` second-order sections
    (conventions: IIR filters)."""
    return _chebyshev2_band(order, attenuation_db, low, high, sample_rate, stop=True)


def elliptic_bandpass(
    order: int,
    ripple_db: float,
    attenuation_db: float,
    low: float,
    high: float,
    sample_rate: float,
) -> NDArray[np.float64]:
    """Elliptic (Cauer) band-pass by the bilinear transform, as second-order sections: pass band
    from ``low`` to ``high`` with ripple ``ripple_db``, stop-band peaks at ``-attenuation_db``
    (conventions: IIR filters)."""
    return _elliptic_band(order, ripple_db, attenuation_db, low, high, sample_rate, stop=False)


def elliptic_bandstop(
    order: int,
    ripple_db: float,
    attenuation_db: float,
    low: float,
    high: float,
    sample_rate: float,
) -> NDArray[np.float64]:
    """Elliptic (Cauer) band-stop by the bilinear transform, as second-order sections: pass bands
    below ``low`` and above ``high`` with ripple ``ripple_db``, stop-band peaks between them at
    ``-attenuation_db`` (conventions: IIR filters)."""
    return _elliptic_band(order, ripple_db, attenuation_db, low, high, sample_rate, stop=True)


def sos_response(
    sos: ArrayLike, frequencies: ArrayLike, sample_rate: float
) -> NDArray[np.complex128]:
    """Complex response of a cascade of second-order sections at each frequency."""
    s = _sos(sos)
    fs = _rate(sample_rate)
    raw = np.asarray(frequencies)
    if raw.dtype.kind not in "iuf":
        raise ValueError("frequencies must be real numbers")
    f = raw.astype(np.float64)
    if f.ndim != 1 or not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be a finite 1-D array")
    zi = np.exp(-2j * np.pi * f / fs)  # z^-1
    h = np.ones(f.size, dtype=np.complex128)
    for b0, b1, b2, a0, a1, a2 in s:
        h *= (b0 + zi * (b1 + zi * b2)) / (a0 + zi * (a1 + zi * a2))
    return h


def sos_group_delay(
    sos: ArrayLike, frequencies: ArrayLike, sample_rate: float
) -> NDArray[np.float64]:
    """Group delay in samples of a cascade of second-order sections: the sum of each section's
    numerator delay minus its denominator's (conventions: IIR filters, Group delay)."""
    s = _sos(sos)
    fs = _rate(sample_rate)
    raw = np.asarray(frequencies)
    if raw.dtype.kind not in "iuf":
        raise ValueError("frequencies must be real numbers")
    f = raw.astype(np.float64)
    if f.ndim != 1 or not np.all(np.isfinite(f)):
        raise ValueError("frequencies must be a finite 1-D array")
    tau = np.zeros(f.size)
    for row in s:
        tau += _poly_delay(row[:3], f / fs) - _poly_delay(row[3:], f / fs)
    return tau


class IirFilter:
    """Causal cascade of second-order sections that keeps its state across chunks (conventions:
    IIR filters).

    The first non-empty chunk fixes the filter as real or complex until :meth:`reset`.
    """

    def __init__(self, sos: ArrayLike) -> None:
        self._sos = _sos(sos)
        self._complex: bool | None = None
        self._state: list[list[Any]] = []

    @property
    def sections(self) -> NDArray[np.float64]:
        """A copy of the sections, each with ``a0 = 1``."""
        return self._sos.copy()

    def reset(self) -> None:
        """Forget every sample seen, as if new."""
        self._complex = None
        self._state = []

    def process(self, chunk: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
        """The next ``len(chunk)`` output samples."""
        a = np.asarray(chunk)
        if a.ndim != 1:
            raise ValueError("chunk must be a 1-D array")
        is_complex = bool(np.iscomplexobj(a))
        dtype = np.complex128 if is_complex else np.float64
        if a.size == 0:
            empty = np.zeros(0, dtype=np.complex128 if self._complex else np.float64)
            return cast("NDArray[np.complex128] | NDArray[np.float64]", empty)
        if self._complex is None:
            self._complex = is_complex
            self._state = [[0.0, 0.0] for _ in self._sos]
        elif self._complex != is_complex:
            kind = "complex" if self._complex else "real"
            raise ValueError(f"this filter takes {kind} samples until reset()")
        y: list[Any] = np.asarray(a, dtype=dtype).tolist()
        for (b0, b1, b2, _, a1, a2), st in zip(self._sos.tolist(), self._state, strict=True):
            s1, s2 = st  # transposed direct form II
            for i, v in enumerate(y):
                out = b0 * v + s1
                s1 = b1 * v - a1 * out + s2
                s2 = b2 * v - a2 * out
                y[i] = out
            st[0], st[1] = s1, s2
        return cast("NDArray[np.complex128] | NDArray[np.float64]", np.array(y, dtype=dtype))


def _steady_pass(sos: list[list[float]], y: list[Any]) -> None:
    """Runs the sections over ``y`` in place, each starting in its steady state for a constant
    input equal to the first sample it sees."""
    u = y[0]
    for b0, b1, b2, _, a1, a2 in sos:
        g = (b0 + b1 + b2) / (1 + a1 + a2)
        s2 = (b2 - a2 * g) * u  # transposed direct form II, as if u had always been the input
        s1 = (b1 - a1 * g) * u + s2
        for i, v in enumerate(y):
            out = b0 * v + s1
            s1 = b1 * v - a1 * out + s2
            s2 = b2 * v - a2 * out
            y[i] = out
        u = g * u


def zero_phase_filter(
    sos: ArrayLike, samples: ArrayLike, pad: int | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """The sections run forward, then backward, over the samples extended by ``pad`` samples of
    odd reflection at each end (default ``3·(2·sections + 1)``); zero phase, magnitude ``|H|²``
    (conventions: IIR filters)."""
    s = _sos(sos)
    if np.any(1 + s[:, 4] + s[:, 5] == 0):
        raise ValueError("every section needs 1 + a1 + a2 != 0 (no pole at z = 1)")
    x = _vector(samples, "samples")
    if not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite: one non-finite sample spoils every output")
    p = 3 * (2 * s.shape[0] + 1) if pad is None else count(pad, "pad")
    if x.size <= p:
        raise ValueError("samples must be longer than pad")
    ext = np.concatenate([2 * x[0] - x[p:0:-1], x, 2 * x[-1] - x[-2 : -p - 2 : -1]])
    y: list[Any] = ext.tolist()
    rows = s.tolist()
    _steady_pass(rows, y)
    y.reverse()
    _steady_pass(rows, y)
    y.reverse()
    return cast(
        "NDArray[np.complex128] | NDArray[np.float64]", np.array(y[p : p + x.size], dtype=x.dtype)
    )


def _factors(up: int, down: int) -> tuple[int, int]:
    """``(up, down)`` checked and reduced by their greatest common divisor."""
    lu, md = count(up, "up"), count(down, "down")
    if lu < 1 or md < 1:
        raise ValueError("up and down must be at least 1")
    g = math.gcd(lu, md)
    return lu // g, md // g


def resample_taps(up: int, down: int) -> NDArray[np.float64]:
    """Default anti-aliasing taps for :func:`resample`: ``fir_lowpass(20R + 1, 1/(2R), 1)``,
    ``R = max(up, down)`` after reduction. Needs ``R > 1``."""
    r = max(_factors(up, down))
    if r == 1:
        raise ValueError("up and down reduce to 1/1, which needs no filter")
    return fir_lowpass(20 * r + 1, 1 / (2 * r), 1)


def resample(
    x: ArrayLike, up: int, down: int, taps: ArrayLike | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Resample by ``up/down`` with the delay removed: output ``m`` is at input time
    ``m * down / up`` (conventions: Resampling)."""
    a = _vector(x, "x")
    if a.size == 0:
        raise ValueError("x must be non-empty")
    lu, md = _factors(up, down)
    if taps is None:
        if lu == md == 1:
            return a.copy()
        h = resample_taps(lu, md)
    else:
        h = _taps(taps)
        if h.size % 2 == 0:
            raise ValueError("resample needs an odd number of taps")
    d = (h.size - 1) // 2
    n_out = -(-a.size * lu // md)
    full = np.convolve(upsample(a, lu), h)
    y = lu * full[d : d + n_out * md : md]
    return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


class Resampler:
    """Causal rational resampler that keeps its state across chunks (conventions: Resampling,
    Streaming resampling). Its stream is ``resample`` with the taps delayed by ``N - 1``.

    The first non-empty chunk fixes the stream as real or complex until :meth:`reset`.
    """

    def __init__(self, up: int, down: int, taps: ArrayLike | None = None) -> None:
        self._l, self._m = _factors(up, down)
        if taps is None:
            h = np.ones(1) if self._l == self._m == 1 else resample_taps(self._l, self._m)
        else:
            h = _taps(taps)
        self._h = h
        t = -(-h.size // self._l)
        poly = np.zeros(self._l * t)
        poly[: h.size] = self._l * h
        self._poly = poly.reshape(t, self._l).T  # row p: L·h[p + t·L], t = 0 … T - 1
        self.reset()

    @property
    def taps(self) -> NDArray[np.float64]:
        """A copy of the taps."""
        return self._h.copy()

    def reset(self) -> None:
        """Forget every sample seen, as if new."""
        self._complex: bool | None = None
        self._count = 0  # inputs so far
        self._next = 0  # index of the next output
        self._hist: NDArray[np.complex128] | NDArray[np.float64] = np.zeros(0)

    def process(self, chunk: ArrayLike) -> NDArray[np.complex128] | NDArray[np.float64]:
        """Every output whose last input is in ``chunk``: ``⌈n·L/M⌉`` in all after ``n`` inputs."""
        a = np.asarray(chunk)
        if a.ndim != 1:
            raise ValueError("chunk must be a 1-D array")
        is_complex = bool(np.iscomplexobj(a))
        x = np.asarray(a, dtype=np.complex128 if is_complex else np.float64)
        if x.size == 0:
            empty = np.zeros(0, dtype=np.complex128 if self._complex else np.float64)
            return cast("NDArray[np.complex128] | NDArray[np.float64]", empty)
        t = self._poly.shape[1]
        if self._complex is None:
            self._complex = is_complex
            self._hist = cast(
                "NDArray[np.complex128] | NDArray[np.float64]", np.zeros(t - 1, dtype=x.dtype)
            )
        elif self._complex != is_complex:
            kind = "complex" if self._complex else "real"
            raise ValueError(f"this resampler takes {kind} samples until reset()")
        buf = np.concatenate([self._hist, x])  # buf[j] is input count - (T - 1) + j
        total = self._count + x.size
        end = -(-total * self._l // self._m)
        m = np.arange(self._next, end, dtype=np.int64) * self._m
        base, phase = m // self._l, m % self._l
        idx = base[:, None] - np.arange(t)[None, :] - (self._count - (t - 1))
        y = np.sum(self._poly[phase] * buf[idx], axis=1)
        self._hist = buf[buf.size - (t - 1) :]
        self._count, self._next = total, end
        return cast("NDArray[np.complex128] | NDArray[np.float64]", y)


def interpolate(
    x: ArrayLike, factor: int, taps: ArrayLike | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``resample(x, factor, 1, taps)``."""
    return resample(x, factor, 1, taps)


def decimate(
    x: ArrayLike, factor: int, taps: ArrayLike | None = None
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``resample(x, 1, factor, taps)``."""
    return resample(x, 1, factor, taps)
