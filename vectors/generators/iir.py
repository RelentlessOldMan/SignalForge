"""Writes vectors/cases/iir.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Butterworth sections come from the real biquad formulas of
conventions: IIR filters (each pole pair's Q, prewarped K, bilinear transform), not from mapping
complex poles as the library does. Chebyshev type I sections come from each analog pole pair's real
quadratic through the bilinear transform, checked against the closed-form magnitude and for
stability. Band-pass and band-stop sections come from the quadratic formula
on each prototype pole's image, and every band design is checked here against the closed-form
magnitude of conventions: IIR filters before it is written. Responses evaluate each section's rational function at
e^(j 2 pi f / fs); filter outputs run each section's difference equation in direct form I, and
zero-phase outputs do the same with each section's past inputs and outputs set to its steady state.

Run from the repo root: python vectors/generators/iir.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
SRC = "vectors/generators/iir.py (stdlib only): "


def butterworth(order, cutoff, fs, high):
    k = math.tan(math.pi * cutoff / fs)
    rows = []
    if order % 2:
        if high:
            rows.append([1 / (k + 1), -1 / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
        else:
            rows.append([k / (k + 1), k / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
    for i in range(order // 2 - 1, -1, -1):
        iq = 2 * math.sin(math.pi * (2 * i + 1) / (2 * order))
        d = k * k + k * iq + 1
        a = [1.0, 2 * (k * k - 1) / d, (k * k - k * iq + 1) / d]
        b = [1 / d, -2 / d, 1 / d] if high else [k * k / d, 2 * k * k / d, k * k / d]
        rows.append(b + a)
    return rows


def cheb_t(n, x):
    if abs(x) <= 1:
        return math.cos(n * math.acos(x))
    return (1 if x > 0 or n % 2 == 0 else -1) * math.cosh(n * math.acosh(abs(x)))


def chebyshev1(order, ripple, cutoff, fs, high):
    eps2 = 10 ** (ripple / 10) - 1
    mu = math.asinh(1 / math.sqrt(eps2)) / order
    k = math.tan(math.pi * cutoff / fs)
    rows = []
    if order % 2:
        q = k * math.sinh(mu)  # low-pass pole -q; the high-pass pole is -k / sinh(mu)
        if high:
            q = k / math.sinh(mu)
            rows.append([1 / (1 + q), -1 / (1 + q), 0.0, 1.0, (q - 1) / (q + 1), 0.0])
        else:
            rows.append([q / (1 + q), q / (1 + q), 0.0, 1.0, (q - 1) / (q + 1), 0.0])
    for i in range(order // 2 - 1, -1, -1):
        phi = math.pi * (2 * i + 1) / (2 * order)
        sigma, omega = -math.sinh(mu) * math.sin(phi), math.cosh(mu) * math.cos(phi)
        m = sigma * sigma + omega * omega
        if high:  # s -> k/s: the pair's quadratic s^2 - 2 sigma' s + m' with
            sigma, m = k * sigma / m, k * k / m
        else:
            sigma, m = k * sigma, k * k * m
        a0 = 1 - 2 * sigma + m
        b = [1 / a0, -2 / a0, 1 / a0] if high else [m / a0, 2 * m / a0, m / a0]
        rows.append(b + [1.0, 2 * (m - 1) / a0, (1 + 2 * sigma + m) / a0])
    if order % 2 == 0:
        rows[0][:3] = [v * 10 ** (-ripple / 20) for v in rows[0][:3]]
    for row in rows:
        assert abs(row[5]) < 1 and abs(row[4]) < 1 + row[5], (order, ripple, cutoff, row)
    freqs = [fs * j / 64 for j in range(1, 32)] + [cutoff]
    for f, h in zip(freqs, response(rows, freqs, fs)):
        t = math.tan(math.pi * f / fs)
        want = 1 / (1 + eps2 * cheb_t(order, k / t if high else t / k) ** 2)
        assert abs(abs(h) ** 2 - want) < 1e-12, (order, ripple, cutoff, high, f)
    return rows


def cheb_design(case_id, order, ripple, cutoff, fs, high, rows=None, src=None):
    op = "chebyshev1_highpass" if high else "chebyshev1_lowpass"
    return {"id": case_id, "op": op,
            "args": {"order": order, "ripple_db": ripple, "cutoff": cutoff, "sample_rate": fs},
            "expected": rows if rows is not None else chebyshev1(order, ripple, cutoff, fs, high),
            "tol": TOL, "source": src or SRC + "each analog pole pair's real quadratic through the "
            "bilinear transform, checked against the closed-form |H|^2 and for stability"}


def chebyshev2(order, atten, cutoff, fs, high):
    """Each section from its analog quadratics: zeros s^2 + W over poles s^2 - 2 sigma s + M (the
    reciprocals of the type I poles), scaled to the cutoff, through s = (1 - z^-1)/(1 + z^-1)."""
    e2 = 1 / (10 ** (atten / 10) - 1)
    mu = math.asinh(1 / math.sqrt(e2)) / order
    k = math.tan(math.pi * cutoff / fs)
    rows = []
    if order % 2:  # type I real pole -sinh(mu); its reciprocal -1/sinh(mu); zero at infinity
        q = k * math.sinh(mu) if high else k / math.sinh(mu)
        if high:
            rows.append([1 / (1 + q), -1 / (1 + q), 0.0, 1.0, (q - 1) / (q + 1), 0.0])
        else:
            rows.append([q / (1 + q), q / (1 + q), 0.0, 1.0, (q - 1) / (q + 1), 0.0])
    for i in range(order // 2 - 1, -1, -1):
        phi = math.pi * (2 * i + 1) / (2 * order)
        sigma, omega = -math.sinh(mu) * math.sin(phi), math.cosh(mu) * math.cos(phi)
        m = sigma * sigma + omega * omega
        if high:  # s -> k/s of the reciprocal pole: the type I pole times k
            sigma, m, w = k * sigma, k * k * m, (k * math.cos(phi)) ** 2
        else:  # the reciprocal pole (sigma - j omega)/m times k; zeros at +-j k/cos(phi)
            sigma, m, w = k * sigma / m, k * k / m, (k / math.cos(phi)) ** 2
        a0 = 1 - 2 * sigma + m
        g = 1 / a0 if high else m / w / a0  # unit gain at s = infinity or s = 0
        rows.append([g * (1 + w), g * 2 * (w - 1), g * (1 + w), 1.0, 2 * (m - 1) / a0,
                     (1 + 2 * sigma + m) / a0])
    for row in rows:
        assert abs(row[5]) < 1 and abs(row[4]) < 1 + row[5], (order, atten, cutoff, row)
    freqs = [fs * j / 64 for j in range(1, 32)] + [cutoff]
    for f, h in zip(freqs, response(rows, freqs, fs)):
        t = math.tan(math.pi * f / fs)
        x = e2 * cheb_t(order, t / k if high else k / t) ** 2
        assert abs(abs(h) ** 2 - x / (1 + x)) < 1e-12, (order, atten, cutoff, high, f)
    assert abs(abs(response(rows, [cutoff], fs)[0]) ** 2 - 10 ** (-atten / 10)) < 1e-12
    return rows


def cheb2_design(case_id, order, atten, cutoff, fs, high, rows=None, src=None):
    op = "chebyshev2_highpass" if high else "chebyshev2_lowpass"
    return {"id": case_id, "op": op,
            "args": {"order": order, "attenuation_db": atten, "cutoff": cutoff, "sample_rate": fs},
            "expected": rows if rows is not None else chebyshev2(order, atten, cutoff, fs, high),
            "tol": TOL, "source": src or SRC + "each section from its analog zero and pole "
            "quadratics through the bilinear transform, checked against the closed-form |H|^2 "
            "and for stability"}


def pmul(p, q):
    out = [0.0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            out[i + j] += a * b
    return out


def padd(p, q):
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else 0.0) + (q[i] if i < len(q) else 0.0) for i in range(n)]


def ppow(p, k):
    out = [1.0]
    for _ in range(k):
        out = pmul(out, p)
    return out


def band_denominator(order, w2, bw, stop):
    """Digital denominator (powers of z^-1, constant term 1) of the band design, from the analog
    prototype prod (S^2 + 2 sin(pi(2i+1)/(2n)) S + 1) [x (S + 1)] with S = (s^2 + w2)/(bw s), or its
    reciprocal for band-stop, cleared of fractions, then s = (1 - z^-1)/(1 + z^-1) cleared of
    (1 + z^-1)^(2n). Ascending powers of s throughout."""
    q = [w2, 0.0, 1.0]  # s^2 + w2
    r = [0.0, bw]  # bw s
    num, den = (r, q) if stop else (q, r)  # S = num/den
    d = [1.0]
    for i in range(order // 2):
        a = 2 * math.sin(math.pi * (2 * i + 1) / (2 * order))
        f = padd(padd(pmul(num, num), [a * v for v in pmul(num, den)]), pmul(den, den))
        d = pmul(d, f)
    if order % 2:
        d = pmul(d, padd(num, den))
    z = [0.0] * (2 * order + 1)
    for k, c in enumerate(d):
        term = pmul(ppow([1.0, -1.0], k), ppow([1.0, 1.0], 2 * order - k))
        z = padd(z, [c * v for v in term])
    return [v / z[0] for v in z]


def band(order, low, high, fs, stop):
    lo, hi = math.tan(math.pi * low / fs), math.tan(math.pi * high / fs)
    w2, bw = lo * hi, hi - lo
    poles = []  # (Re s, |s|^2) of each section's analog pole pair, in section order
    if order % 2:
        poles.append((-bw / 2, w2))  # s^2 + bw s + w2, real or complex roots alike
    for i in range(order // 2 - 1, -1, -1):
        theta = math.pi / 2 + math.pi * (2 * i + 1) / (2 * order)
        p = complex(math.cos(theta), math.sin(theta))
        c = bw / p if stop else bw * p
        d = cmath.sqrt(c * c - 4 * w2)
        pair = [(c + d) / 2, (c - d) / 2]
        poles += [(s.real, abs(s) ** 2) for s in sorted(pair, key=abs)]
    rows = []
    for sigma, m in poles:
        a0 = 1 - 2 * sigma + m
        b = [(1 + w2) / a0, 2 * (w2 - 1) / a0, (1 + w2) / a0] if stop else [bw / a0, 0.0, -bw / a0]
        rows.append(b + [1.0, 2 * (m - 1) / a0, (1 + 2 * sigma + m) / a0])
    for row in rows:  # stable: both poles inside the unit circle
        assert abs(row[5]) < 1 and abs(row[4]) < 1 + row[5], (order, low, high, row)
    prod = [1.0]
    for row in rows:
        prod = pmul(prod, row[3:])
    want = band_denominator(order, w2, bw, stop)
    assert all(abs(a - b) <= 1e-9 * max(map(abs, want)) for a, b in zip(prod, want)), (order, low)
    freqs = [fs * k / 64 for k in range(1, 32)] + [low, high, fs / math.pi * math.atan(w2 ** 0.5)]
    for f, h in zip(freqs, response(rows, freqs, fs)):
        t = math.tan(math.pi * f / fs)
        x = (t * t - w2) / (bw * t)
        want = x ** (2 * order) / (1 + x ** (2 * order)) if stop else 1 / (1 + x ** (2 * order))
        assert abs(abs(h) ** 2 - want) < 1e-12, (order, low, high, fs, stop, f)
    return rows


def band_design(case_id, order, low, high, fs, stop, rows=None, src=None):
    op = "butterworth_bandstop" if stop else "butterworth_bandpass"
    return {"id": case_id, "op": op,
            "args": {"order": order, "low": low, "high": high, "sample_rate": fs},
            "expected": rows if rows is not None else band(order, low, high, fs, stop),
            "tol": TOL, "source": src or SRC + "quadratic formula on each prototype pole's image, "
            "checked against the closed-form |H|^2, section stability, and the product of the "
            "denominators against the analog prototype expanded by polynomial substitution"}


def response(sos, freqs, fs):
    out = []
    for f in freqs:
        zi = cmath.exp(-2j * math.pi * f / fs)
        h = 1 + 0j
        for b0, b1, b2, a0, a1, a2 in sos:
            h *= (b0 + b1 * zi + b2 * zi * zi) / (a0 + a1 * zi + a2 * zi * zi)
        out.append(h)
    return out


def run(sos, x):
    y = list(x)
    for b0, b1, b2, a0, a1, a2 in sos:
        b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
        x1 = x2 = y1 = y2 = 0
        for n, v in enumerate(y):
            out = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, v, y1, out
            y[n] = out
    return y


def steady(sos, y):
    u = y[0]
    for b0, b1, b2, a0, a1, a2 in sos:
        b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
        g = (b0 + b1 + b2) / (1 + a1 + a2)
        x1 = x2 = u
        y1 = y2 = g * u
        for n, v in enumerate(y):
            out = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, v, y1, out
            y[n] = out
        u = g * u


def zero_phase(sos, x, pad=None):
    p = 3 * (2 * len(sos) + 1) if pad is None else pad
    n = len(x)
    ext = [2 * x[0] - x[p - i] for i in range(p)] + list(x)
    ext += [2 * x[-1] - x[n - 2 - i] for i in range(p)]
    steady(sos, ext)
    ext.reverse()
    steady(sos, ext)
    ext.reverse()
    return ext[p:p + n]


def zp(case_id, sos, x, pad=None, expected=None, src=None):
    args = {"sos": sos, "samples": samples(x)}
    if pad is not None:
        args["pad"] = pad
    y = expected if expected is not None else zero_phase(sos, x, pad)
    return {"id": case_id, "op": "zero_phase_filter", "args": args, "expected": samples(y),
            "tol": TOL, "source": src or SRC + "direct form I both ways, each pass from the "
            "sections' steady state, over the odd extension"}


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


def samples(x):
    return cplx(x) if any(isinstance(v, complex) for v in x) else x


def design(case_id, order, cutoff, fs, high, rows=None, src=None):
    op = "butterworth_highpass" if high else "butterworth_lowpass"
    return {"id": case_id, "op": op, "args": {"order": order, "cutoff": cutoff, "sample_rate": fs},
            "expected": rows if rows is not None else butterworth(order, cutoff, fs, high),
            "tol": TOL, "source": src or SRC + "real biquad formulas from each pole pair's Q"}


def resp(case_id, sos, freqs, fs, expected=None, src=None):
    return {"id": case_id, "op": "sos_response",
            "args": {"sos": sos, "frequencies": freqs, "sample_rate": fs},
            "expected": cplx(expected if expected is not None else response(sos, freqs, fs)),
            "tol": TOL, "source": src or SRC + "each section's rational function at e^(j 2 pi f/fs)"}


def filt(case_id, sos, x, chunks, expected=None, src=None):
    y = expected if expected is not None else run(sos, x)
    return {"id": case_id, "op": "iir_filter",
            "args": {"sos": sos, "samples": samples(x), "chunks": chunks},
            "expected": samples(y), "tol": TOL,
            "source": src or SRC + "difference equations in direct form I, section by section"}


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


r2 = math.sqrt(2)
c2 = math.sqrt(r2 - 1)  # Chebyshev order 2, ripple 10 log10 2 dB (eps = 1), K = 1: s^2 + c2 s + 1/r2
cd = 1 + c2 + 1 / r2
ch3 = chebyshev1(3, 0.5, 0.1, 1.0, False)
c2s = math.sqrt((math.sqrt(2) - 1) / 2)  # sinh(asinh(1)/2)
c2d = 1 + 2 * c2s + math.sqrt(2)
c2b = math.sqrt(2) / 2 / c2d
cb4 = chebyshev2(4, 40.0, 0.2, 1.0, False)
ramp = [float(i % 5) - 2 + 0.25 * math.sin(0.7 * i) for i in range(24)]
chirp = [cmath.exp(1j * (0.3 * i + 0.02 * i * i)) * (1 + 0.1 * i) for i in range(20)]
lp4 = butterworth(4, 1000.0, 8000.0, False)
hp3 = butterworth(3, 0.15, 1.0, True)
pole_half = [[1.0, 0.0, 0.0, 1.0, -0.5, 0.0]]
bp3 = band(3, 1000.0, 3000.0, 16000.0, False)
bs2 = band(2, 0.2, 0.3, 1.0, True)
bad_a0 = [[1.0, 0.0, 0.0, 0.0, -0.5, 0.0]]
short_row = [[1.0, 0.0, 0.0, 1.0, -0.5]]
edges = [0.0, 500.0, 1000.0, 2500.0, 4000.0, -1000.0]

cases = [
    design("butterworth.lowpass_2_quarter", 2, 2000.0, 8000.0, False,
           rows=[[1 - r2 / 2, 2 - r2, 1 - r2 / 2, 1.0, 0.0, 3 - 2 * r2]],
           src="by hand: K = tan(pi/4) = 1, 1/Q = sqrt 2, D = 2 + sqrt 2; b = [1, 2, 1]/D = "
           "(1 - sqrt 2/2)[1, 2, 1], a1 = 0, a2 = (2 - sqrt 2)/(2 + sqrt 2) = 3 - 2 sqrt 2"),
    design("butterworth.lowpass_1", 1, 1000.0, 8000.0, False),
    design("butterworth.lowpass_3", 3, 1000.0, 8000.0, False),
    design("butterworth.lowpass_4", 4, 1000.0, 8000.0, False),
    design("butterworth.lowpass_7_narrow", 7, 0.01, 1.0, False),
    design("butterworth.highpass_1", 1, 300.0, 48000.0, True),
    design("butterworth.highpass_2", 2, 0.25, 1.0, True),
    design("butterworth.highpass_5", 5, 0.15, 1.0, True),
    design("butterworth.highpass_6_wide", 6, 0.45, 1.0, True),
    err("butterworth.order_zero", "butterworth_lowpass",
        {"order": 0, "cutoff": 1.0, "sample_rate": 8.0}, "order >= 1 required"),
    err("butterworth.order_negative", "butterworth_highpass",
        {"order": -2, "cutoff": 1.0, "sample_rate": 8.0}, "order >= 1 required"),
    err("butterworth.cutoff_zero", "butterworth_lowpass",
        {"order": 2, "cutoff": 0.0, "sample_rate": 8.0}, "0 < cutoff < sample_rate/2 required"),
    err("butterworth.cutoff_nyquist", "butterworth_highpass",
        {"order": 2, "cutoff": 4.0, "sample_rate": 8.0}, "0 < cutoff < sample_rate/2 required"),
    err("butterworth.rate_zero", "butterworth_lowpass",
        {"order": 2, "cutoff": 1.0, "sample_rate": 0.0}, "sample_rate must be positive"),
    err("butterworth.cutoff_above_nyquist", "butterworth_lowpass",
        {"order": 2, "cutoff": 5.0, "sample_rate": 8.0}, "0 < cutoff < sample_rate/2 required"),
    err("butterworth.cutoff_nan", "butterworth_highpass",
        {"order": 2, "cutoff": "nan", "sample_rate": 8.0}, "the cutoff must be finite"),
    err("butterworth.rate_nan", "butterworth_lowpass",
        {"order": 2, "cutoff": 1.0, "sample_rate": "nan"}, "sample_rate must be finite"),
    band_design("butterworth.bandpass_1_by_hand", 1, 1.0, 3.0, 8.0, False,
                rows=[[0.5, 0.0, -0.5, 1.0, 0.0, 0.0]],
                src="by hand: tan(pi/8) tan(3 pi/8) = 1 and tan(3 pi/8) - tan(pi/8) = 2, so the "
                "analog section is 2s/(s^2 + 2s + 1); with s = (1 - z^-1)/(1 + z^-1) that is "
                "2(1 - z^-2)/4"),
    band_design("butterworth.bandstop_1_by_hand", 1, 1.0, 3.0, 8.0, True,
                rows=[[0.5, 0.0, 0.5, 1.0, 0.0, 0.0]],
                src="by hand: as bandpass_1_by_hand, the analog section (s^2 + 1)/(s^2 + 2s + 1) "
                "is (2 + 2 z^-2)/4"),
    band_design("butterworth.bandpass_2", 2, 1000.0, 2000.0, 8000.0, False),
    band_design("butterworth.bandpass_3", 3, 1000.0, 3000.0, 16000.0, False),
    band_design("butterworth.bandpass_4_narrow", 4, 0.1, 0.11, 1.0, False),
    band_design("butterworth.bandpass_5_wide", 5, 0.02, 0.45, 1.0, False),
    band_design("butterworth.bandstop_2", 2, 0.2, 0.3, 1.0, True),
    band_design("butterworth.bandstop_3", 3, 50.0, 70.0, 1000.0, True),
    band_design("butterworth.bandstop_6", 6, 3000.0, 9000.0, 48000.0, True),
    cheb_design("chebyshev1.lowpass_1_by_hand", 1, 10 * math.log10(1.25), 2.0, 8.0, False,
                rows=[[2 / 3, 2 / 3, 0.0, 1.0, 1 / 3, 0.0]],
                src="by hand: eps = 1/2, so the order-1 prototype pole is -sinh(asinh 2) = -2; K = "
                "tan(pi/4) = 1, pole -2, H(s) = 2/(s + 2); s = (1 - z^-1)/(1 + z^-1) gives "
                "(2/3)(1 + z^-1)/(1 + z^-1/3)"),
    cheb_design("chebyshev1.lowpass_2_by_hand", 2, 10 * math.log10(2), 2.0, 8.0, False,
                rows=[[0.5 / cd, 1 / cd, 0.5 / cd, 1.0, (2 / r2 - 2) / cd, (1 - c2 + 1 / r2) / cd]],
                src="by hand: eps = 1, mu = asinh(1)/2, sinh^2 mu = (sqrt2 - 1)/2, cosh^2 mu = "
                "(sqrt2 + 1)/2; the pole at 3pi/4 gives s^2 + sqrt(sqrt2 - 1) s + 1/sqrt2; DC gain "
                "1/sqrt2 makes the numerator 1/2; K = 1 and the bilinear transform"),
    cheb_design("chebyshev1.lowpass_3", 3, 0.5, 0.1, 1.0, False),
    cheb_design("chebyshev1.lowpass_4", 4, 1.0, 1000.0, 8000.0, False),
    cheb_design("chebyshev1.lowpass_7_narrow", 7, 0.1, 0.02, 1.0, False),
    cheb_design("chebyshev1.lowpass_8_big_ripple", 8, 6.0, 12000.0, 48000.0, False),
    cheb_design("chebyshev1.highpass_1", 1, 2.0, 300.0, 8000.0, True),
    cheb_design("chebyshev1.highpass_2", 2, 0.25, 0.3, 1.0, True),
    cheb_design("chebyshev1.highpass_5", 5, 1.0, 0.15, 1.0, True),
    cheb_design("chebyshev1.highpass_6_wide", 6, 3.0, 0.45, 1.0, True),
    err("chebyshev1.ripple_zero", "chebyshev1_lowpass",
        {"order": 2, "ripple_db": 0.0, "cutoff": 1.0, "sample_rate": 8.0}, "ripple_db > 0 required"),
    err("chebyshev1.ripple_negative", "chebyshev1_highpass",
        {"order": 2, "ripple_db": -1.0, "cutoff": 1.0, "sample_rate": 8.0},
        "ripple_db > 0 required"),
    err("chebyshev1.ripple_nan", "chebyshev1_lowpass",
        {"order": 2, "ripple_db": "nan", "cutoff": 1.0, "sample_rate": 8.0},
        "ripple_db must be finite"),
    err("chebyshev1.ripple_inf", "chebyshev1_highpass",
        {"order": 2, "ripple_db": "inf", "cutoff": 1.0, "sample_rate": 8.0},
        "ripple_db must be finite"),
    err("chebyshev1.order_zero", "chebyshev1_lowpass",
        {"order": 0, "ripple_db": 1.0, "cutoff": 1.0, "sample_rate": 8.0}, "order >= 1 required"),
    err("chebyshev1.cutoff_nyquist", "chebyshev1_highpass",
        {"order": 2, "ripple_db": 1.0, "cutoff": 4.0, "sample_rate": 8.0},
        "0 < cutoff < sample_rate/2 required"),
    err("chebyshev1.cutoff_zero", "chebyshev1_lowpass",
        {"order": 2, "ripple_db": 1.0, "cutoff": 0.0, "sample_rate": 8.0},
        "0 < cutoff < sample_rate/2 required"),
    err("chebyshev1.rate_zero", "chebyshev1_lowpass",
        {"order": 2, "ripple_db": 1.0, "cutoff": 1.0, "sample_rate": 0.0},
        "sample_rate must be positive"),
    cheb2_design("chebyshev2.lowpass_1_by_hand", 1, 10 * math.log10(2), 2.0, 8.0, False,
                 rows=[[0.5, 0.5, 0.0, 1.0, 0.0, 0.0]],
                 src="by hand: 10^(A/10) = 2 gives eps = 1 and sinh(mu) = 1, so the prototype pole "
                 "is -1/sinh(mu) = -1 with its zero at infinity; K = tan(pi/4) = 1, H(s) = 1/(s + 1), "
                 "through the bilinear transform (1 + z^-1)/2"),
    cheb2_design("chebyshev2.lowpass_2_by_hand", 2, 10 * math.log10(2), 2.0, 8.0, False,
                 rows=[[3 * c2b, 2 * c2b, 3 * c2b, 1.0, 2 * (math.sqrt(2) - 1) / c2d,
                        (1 - 2 * c2s + math.sqrt(2)) / c2d]],
                 src="by hand: eps = 1, mu = asinh(1)/2, s = sinh mu = sqrt((sqrt2 - 1)/2), "
                 "sinh^2 + cosh^2 = sqrt2; the type I pair at 3pi/4 has |p|^2 = 1/sqrt2 and real part "
                 "-s/sqrt2, so the reciprocal pair is s^2 + 2s s + sqrt2; zeros at +-j/cos(pi/4): "
                 "s^2 + 2; DC gain 1 needs a factor sqrt2/2; K = 1, then s = (1 - z^-1)/(1 + z^-1): "
                 "numerator (sqrt2/2)[3, 2, 3], denominator [1 + 2s + sqrt2, 2(sqrt2 - 1), "
                 "1 - 2s + sqrt2]"),
    cheb2_design("chebyshev2.lowpass_3", 3, 40.0, 0.1, 1.0, False),
    cheb2_design("chebyshev2.lowpass_4", 4, 40.0, 0.2, 1.0, False),
    cheb2_design("chebyshev2.lowpass_5_audio", 5, 60.0, 4000.0, 48000.0, False),
    cheb2_design("chebyshev2.lowpass_8_narrow", 8, 80.0, 0.03, 1.0, False),
    cheb2_design("chebyshev2.highpass_1", 1, 20.0, 300.0, 8000.0, True),
    cheb2_design("chebyshev2.highpass_2", 2, 30.0, 0.3, 1.0, True),
    cheb2_design("chebyshev2.highpass_5", 5, 50.0, 0.1, 1.0, True),
    cheb2_design("chebyshev2.highpass_6_wide", 6, 20.0, 0.45, 1.0, True),
    err("chebyshev1.ripple_over_200", "chebyshev1_lowpass",
        {"order": 2, "ripple_db": 200.5, "cutoff": 1.0, "sample_rate": 8.0}, "0 < ripple_db <= 200 required"),
    err("chebyshev1.ripple_huge", "chebyshev1_highpass",
        {"order": 2, "ripple_db": 4000.0, "cutoff": 1.0, "sample_rate": 8.0}, "0 < ripple_db <= 200 required (10^(R/10) would overflow)"),
    err("chebyshev2.attenuation_zero", "chebyshev2_lowpass",
        {"order": 2, "attenuation_db": 0.0, "cutoff": 1.0, "sample_rate": 8.0}, "attenuation_db > 0 required"),
    err("chebyshev2.attenuation_negative", "chebyshev2_highpass",
        {"order": 2, "attenuation_db": -20.0, "cutoff": 1.0, "sample_rate": 8.0}, "attenuation_db > 0 required"),
    err("chebyshev2.attenuation_nan", "chebyshev2_lowpass",
        {"order": 2, "attenuation_db": "nan", "cutoff": 1.0, "sample_rate": 8.0}, "attenuation_db must be finite"),
    err("chebyshev2.attenuation_over_200", "chebyshev2_highpass",
        {"order": 2, "attenuation_db": 200.5, "cutoff": 1.0, "sample_rate": 8.0}, "attenuation_db <= 200 required"),
    err("chebyshev2.order_zero", "chebyshev2_lowpass",
        {"order": 0, "attenuation_db": 40.0, "cutoff": 1.0, "sample_rate": 8.0}, "order >= 1 required"),
    err("chebyshev2.cutoff_nyquist", "chebyshev2_lowpass",
        {"order": 2, "attenuation_db": 40.0, "cutoff": 4.0, "sample_rate": 8.0}, "0 < cutoff < sample_rate/2 required"),
    err("chebyshev2.rate_inf", "chebyshev2_highpass",
        {"order": 2, "attenuation_db": 40.0, "cutoff": 1.0, "sample_rate": "inf"}, "sample_rate must be finite"),
    resp("sos_response.chebyshev2_lowpass_4", cb4, [0.0, 0.1, 0.2, 0.3, 0.5], 1.0),
    resp("sos_response.chebyshev1_lowpass_3", ch3, [0.0, 0.05, 0.1, 0.2, 0.5], 1.0),
    filt("iir_filter.chebyshev1_lowpass_chunks", ch3, ramp, [7, 17]),
    band_design("butterworth.bandstop_3_wide", 3, 0.02, 0.45, 1.0, True),
    err("butterworth.band_low_negative", "butterworth_bandstop",
        {"order": 2, "low": -1.0, "high": 2.0, "sample_rate": 8.0}, "0 < low required"),
    err("butterworth.band_high_above_nyquist", "butterworth_bandpass",
        {"order": 2, "low": 1.0, "high": 5.0, "sample_rate": 8.0}, "high < sample_rate/2 required"),
    err("butterworth.band_low_inf", "butterworth_bandstop",
        {"order": 2, "low": "-inf", "high": 2.0, "sample_rate": 8.0}, "the edges must be finite"),
    err("butterworth.band_rate_zero", "butterworth_bandstop",
        {"order": 2, "low": 1.0, "high": 2.0, "sample_rate": 0.0}, "sample_rate must be positive"),
    err("butterworth.band_rate_negative", "butterworth_bandpass",
        {"order": 2, "low": 1.0, "high": 2.0, "sample_rate": -8.0}, "sample_rate must be positive"),
    err("butterworth.band_rate_nan", "butterworth_bandpass",
        {"order": 2, "low": 1.0, "high": 2.0, "sample_rate": "nan"}, "sample_rate must be finite"),
    err("butterworth.band_order_negative", "butterworth_bandstop",
        {"order": -1, "low": 1.0, "high": 2.0, "sample_rate": 8.0}, "order >= 1 required"),
    err("butterworth.band_low_above_high", "butterworth_bandpass",
        {"order": 2, "low": 2.0, "high": 1.0, "sample_rate": 8.0}, "low < high required"),
    err("butterworth.band_low_equals_high", "butterworth_bandstop",
        {"order": 2, "low": 1.0, "high": 1.0, "sample_rate": 8.0}, "low < high required"),
    err("butterworth.band_low_zero", "butterworth_bandpass",
        {"order": 2, "low": 0.0, "high": 1.0, "sample_rate": 8.0}, "0 < low required"),
    err("butterworth.band_high_nyquist", "butterworth_bandstop",
        {"order": 2, "low": 1.0, "high": 4.0, "sample_rate": 8.0}, "high < sample_rate/2 required"),
    err("butterworth.band_order_zero", "butterworth_bandpass",
        {"order": 0, "low": 1.0, "high": 2.0, "sample_rate": 8.0}, "order >= 1 required"),
    err("butterworth.band_high_nan", "butterworth_bandpass",
        {"order": 2, "low": 1.0, "high": "nan", "sample_rate": 8.0}, "the edges must be finite"),
    resp("sos_response.butterworth_bandpass_3", bp3,
         [0.0, 500.0, 1000.0, 1732.0, 3000.0, 5000.0, 8000.0], 16000.0),
    resp("sos_response.butterworth_bandstop_2", bs2, [0.0, 0.2, 0.245, 0.3, 0.5], 1.0),
    filt("iir_filter.butterworth_bandpass_chunks", bp3, ramp, [5, 19]),
    zp("zero_phase.average_by_hand", [[0.5, 0.5, 0.0, 1.0, 0.0, 0.0]], [1.0, 2.0, 4.0], pad=0,
       expected=[1.25, 2.25, 3.0],
       src="by hand: y[n] = (x[n] + x[n-1])/2 with x[-1] = x[0]: forward 1, 1.5, 3; backward "
       "from 3: 3, 2.25, 1.25; reversed 1.25, 2.25, 3"),
    zp("zero_phase.average_pad_by_hand", [[0.5, 0.5, 0.0, 1.0, 0.0, 0.0]], [1.0, 2.0, 4.0], pad=1,
       expected=[1.0, 2.25, 4.0],
       src="by hand: extended 0, 1, 2, 4, 6; forward from 0: 0, 0.5, 1.5, 3, 5; backward from 5: "
       "5, 4, 2.25, 1, 0.25; the middle three reversed: 1, 2.25, 4"),
    zp("zero_phase.constant_lowpass", lp4, [3.0] * 30, expected=[3.0] * 30,
       src="analytic: each pass starts in the steady state of a constant, so a low-pass (gain 1 "
       "at DC) gives the constant back exactly, to rounding"),
    zp("zero_phase.lowpass_default_pad", lp4, ramp),
    zp("zero_phase.bandpass_no_pad", bp3, ramp, pad=0),
    zp("zero_phase.highpass_complex", hp3, chirp, pad=4),
    zp("zero_phase.pad_one_short", lp4, ramp[:16], pad=15),
    zp("zero_phase.bandstop_gains", bs2, ramp),
    zp("zero_phase.one_sample", lp4, [2.5], pad=0, expected=[2.5],
       src="analytic: one sample is a constant, and a low-pass with unit DC gain started in its "
       "steady state gives it back"),
    err("zero_phase.pole_at_one_second", "zero_phase_filter",
        {"sos": [[1.0, 0.0, 0.0, 1.0, -0.5, 0.0], [1.0, 0.0, 0.0, 1.0, -1.0, 0.0]],
         "samples": ramp, "pad": 0}, "the second section has a pole at z = 1"),
    err("zero_phase.pole_at_one_after_a0", "zero_phase_filter",
        {"sos": [[2.0, 0.0, 0.0, 2.0, -2.0, 0.0]], "samples": ramp, "pad": 0},
        "divided by a0 = 2 the section has a pole at z = 1"),
    err("zero_phase.a0_zero", "zero_phase_filter", {"sos": bad_a0, "samples": ramp, "pad": 0},
        "every a0 must be nonzero"),
    err("zero_phase.no_sections", "zero_phase_filter", {"sos": [], "samples": ramp, "pad": 0},
        "at least one section required"),
    err("zero_phase.short_row", "zero_phase_filter", {"sos": short_row, "samples": ramp, "pad": 0},
        "rows of 6 required"),
    err("zero_phase.coefficient_nan", "zero_phase_filter",
        {"sos": [[1.0, "nan", 0.0, 1.0, 0.0, 0.0]], "samples": ramp, "pad": 0},
        "coefficients must be finite"),
    err("zero_phase.sample_nan", "zero_phase_filter",
        {"sos": lp4, "samples": ramp[:5] + ["nan"] + ramp[6:]}, "samples must be finite"),
    err("zero_phase.pad_too_long", "zero_phase_filter",
        {"sos": lp4, "samples": ramp[:15], "pad": 15}, "samples must be longer than pad"),
    err("zero_phase.default_pad_too_long", "zero_phase_filter",
        {"sos": lp4, "samples": ramp[:15]}, "samples must be longer than the default pad, 15"),
    err("zero_phase.pad_negative", "zero_phase_filter",
        {"sos": lp4, "samples": ramp, "pad": -1}, "pad >= 0 required"),
    err("zero_phase.pole_at_one", "zero_phase_filter",
        {"sos": [[1.0, 0.0, 0.0, 1.0, -1.0, 0.0]], "samples": ramp, "pad": 0},
        "a pole at z = 1 has no steady state"),
    err("zero_phase.empty", "zero_phase_filter", {"sos": lp4, "samples": [], "pad": 0},
        "samples must be non-empty"),
    resp("sos_response.one_pole", pole_half, [0.0, 0.25, 0.5], 1.0,
         expected=[2 + 0j, 1 / (1 + 0.5j), 2 / 3 + 0j],
         src="by hand: H = 1/(1 - 0.5 z^-1); z^-1 = 1, -j, -1 at f = 0, fs/4, fs/2 gives 2, "
         "1/(1 + 0.5j), 2/3"),
    resp("sos_response.a0_divided", [[2.0, 0.0, 0.0, 2.0, -1.0, 0.0]], [0.0, 0.5], 1.0,
         expected=[2 + 0j, 2 / 3 + 0j],
         src="by hand: the row divided by a0 = 2 is 1/(1 - 0.5 z^-1): 2 at DC, 2/3 at fs/2"),
    resp("sos_response.butterworth_lowpass_4", lp4, edges, 8000.0),
    resp("sos_response.butterworth_highpass_3", hp3, [0.0, 0.05, 0.15, 0.3, 0.5], 1.0),
    err("sos_response.a0_zero", "sos_response",
        {"sos": bad_a0, "frequencies": [0.0], "sample_rate": 1.0}, "every a0 must be nonzero"),
    err("sos_response.short_row", "sos_response",
        {"sos": short_row, "frequencies": [0.0], "sample_rate": 1.0}, "rows of 6 required"),
    err("sos_response.no_sections", "sos_response",
        {"sos": [], "frequencies": [0.0], "sample_rate": 1.0}, "at least one section required"),
    err("sos_response.coefficient_inf", "sos_response",
        {"sos": [[1.0, "inf", 0.0, 1.0, 0.0, 0.0]], "frequencies": [0.0], "sample_rate": 1.0},
        "coefficients must be finite"),
    err("sos_response.frequency_nan", "sos_response",
        {"sos": [[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]], "frequencies": ["nan"], "sample_rate": 1.0},
        "frequencies must be finite"),
    filt("iir_filter.one_pole_impulse", [[0.5, 0.0, 0.0, 1.0, -0.5, 0.0]],
         [1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2, 4], expected=[0.5 ** (n + 1) for n in range(6)],
         src="by hand: y[n] = 0.5 x[n] + 0.5 y[n-1] with an impulse gives 0.5^(n+1)"),
    filt("iir_filter.biquad_step", [[1.0, 2.0, 1.0, 4.0, 0.0, 0.0]], [1.0] * 4, [4],
         expected=[0.25, 0.75, 1.0, 1.0],
         src="by hand: the row divided by a0 = 4 is the FIR [1, 2, 1]/4; a unit step gives "
         "0.25, 0.75, 1, 1"),
    filt("iir_filter.butterworth_real_chunks", lp4, ramp, [3, 0, 10, 11]),
    filt("iir_filter.butterworth_real_whole", lp4, ramp, [24]),
    filt("iir_filter.butterworth_complex_chunks", hp3, chirp, [1, 1, 18]),
    err("iir_filter.a0_zero", "iir_filter", {"sos": bad_a0, "samples": [1.0], "chunks": [1]},
        "every a0 must be nonzero"),
    err("iir_filter.no_sections", "iir_filter", {"sos": [], "samples": [1.0], "chunks": [1]},
        "at least one section required"),
]

doc = {
    "schema": 1,
    "suite": "iir",
    "description": "IIR filters: Butterworth designs, section responses and the streaming filter "
    "(conventions: IIR filters).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "iir.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/iir.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
