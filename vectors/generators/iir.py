"""Writes vectors/cases/iir.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Butterworth sections come from the real biquad formulas of
conventions: IIR filters (each pole pair's Q, prewarped K, bilinear transform), not from mapping
complex poles as the library does. Responses evaluate each section's rational function at
e^(j 2 pi f / fs); filter outputs run each section's difference equation in direct form I.

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
ramp = [float(i % 5) - 2 + 0.25 * math.sin(0.7 * i) for i in range(24)]
chirp = [cmath.exp(1j * (0.3 * i + 0.02 * i * i)) * (1 + 0.1 * i) for i in range(20)]
lp4 = butterworth(4, 1000.0, 8000.0, False)
hp3 = butterworth(3, 0.15, 1.0, True)
pole_half = [[1.0, 0.0, 0.0, 1.0, -0.5, 0.0]]
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
