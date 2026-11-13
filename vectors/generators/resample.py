"""Writes vectors/cases/resample.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Default taps are the windowed sinc evaluated term by term
(vectors/generators/fir.py checks that closed form against numerical integration), and each output
sample is the conventions sum y[m] = L * sum_k h[k] u[m*M + D - k], evaluated by brute force over
every k with the zero-stuffed signal built explicitly.

Run from the repo root: python vectors/generators/resample.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 0}


def sinc(x):
    return 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)


def default_taps(up, down):
    g = math.gcd(up, down)
    r = max(up // g, down // g)
    n, nu = 20 * r + 1, 1 / (2 * r)
    h = []
    for i in range(n):
        t = i - (n - 1) / 2
        w = 0.54 - 0.46 * math.cos(2 * math.pi * i / (n - 1))
        h.append(2 * nu * sinc(2 * nu * t) * w)
    s = math.fsum(h)
    return [v / s for v in h]


def resample(x, up, down, h):
    g = math.gcd(up, down)
    lu, md = up // g, down // g
    u = [0.0] * (len(x) * lu)
    for i, v in enumerate(x):
        u[i * lu] = v
    d = (len(h) - 1) // 2
    n_out = -(-len(x) * lu // md)
    y = []
    for m in range(n_out):
        terms = []
        for k in range(len(h)):
            j = m * md + d - k
            if 0 <= j < len(u):
                terms.append(h[k] * u[j])
        if any(isinstance(t, complex) for t in terms):
            y.append(lu * complex(math.fsum(t.real for t in terms), math.fsum(t.imag for t in terms)))
        else:
            y.append(lu * math.fsum(terms))
    return y


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


SRC = (
    "vectors/generators/resample.py (stdlib only): the conventions sum evaluated term by term "
    "over the explicitly zero-stuffed input"
)


def gen(case_id, op, args, x, up, down, taps_used, src=SRC):
    y = resample(x, up, down, taps_used)
    expected = cplx(y) if any(isinstance(v, complex) for v in y) else y
    return {"id": case_id, "op": op, "args": args, "expected": expected, "tol": TOL, "source": src}


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


ramp = [float(i % 7) - 3 for i in range(40)]
tone = [math.cos(2 * math.pi * 0.07 * n + 0.3) for n in range(48)]
ctone = [complex(math.cos(0.4 * n), math.sin(0.4 * n)) for n in range(30)]
lin = [0.25, 0.5, 0.25]

cases = [
    {"id": "interpolate.linear", "op": "interpolate",
     "args": {"x": [1, 2, 3], "factor": 2, "taps": lin}, "expected": [1, 1.5, 2, 2.5, 3, 1.5],
     "tol": TOL, "source": "by hand: 2*[0.25 0.5 0.25] is linear interpolation; the last sample "
     "meets the zero after the input, (3 + 0)/2"},
    {"id": "decimate.smooth", "op": "decimate",
     "args": {"x": [1, 2, 3, 4, 5, 6], "factor": 2, "taps": lin}, "expected": [1, 3, 5],
     "tol": TOL, "source": "by hand: y[m] = 0.25 x[2m-1] + 0.5 x[2m] + 0.25 x[2m+1], x[-1] = 0: "
     "0.5 + 0.5, 0.5 + 1.5 + 1, 1 + 2.5 + 1.5"},
    {"id": "resample.gcd", "op": "resample",
     "args": {"x": [1, 2, 3], "up": 4, "down": 2, "taps": lin}, "expected": [1, 1.5, 2, 2.5, 3, 1.5],
     "tol": TOL, "source": "4/2 reduces to 2/1, so this is interpolate.linear"},
    {"id": "resample.single_tap_gain", "op": "resample",
     "args": {"x": [1, -2], "up": 2, "down": 1, "taps": [1]}, "expected": [2, 0, -4, 0], "tol": TOL,
     "source": "by hand: with h = [1] the output is up times the zero-stuffed input"},
    {"id": "resample.identity_default", "op": "resample",
     "args": {"x": [1, 2, 3], "up": 3, "down": 3}, "expected": [1, 2, 3], "tol": TOL,
     "source": "3/3 reduces to 1/1, which with no taps returns x"},
    {"id": "resample.identity_delay_taps", "op": "resample",
     "args": {"x": [4, 5, 6], "up": 1, "down": 1, "taps": [0, 1, 0]}, "expected": [4, 5, 6],
     "tol": TOL, "source": "a centered unit impulse with its delay removed is the identity"},
    {"id": "decimate.complex", "op": "decimate",
     "args": {"x": {"re": [1, 0, 1, 0], "im": [0, 1, 0, 1]}, "factor": 2, "taps": lin},
     "expected": {"re": [0.5, 0.5], "im": [0.25, 0.5]}, "tol": TOL,
     "source": "by hand, x = [1, j, 1, j]: y0 = 0.5*1 + 0.25j, y1 = 0.25j + 0.5*1 + 0.25j"},
    gen("resample.3_2_default", "resample", {"x": ramp, "up": 3, "down": 2}, ramp, 3, 2,
        default_taps(3, 2)),
    gen("decimate.3_default", "decimate", {"x": tone, "factor": 3}, tone, 1, 3, default_taps(1, 3)),
    gen("interpolate.4_default", "interpolate", {"x": tone[:12], "factor": 4}, tone[:12], 4, 1,
        default_taps(4, 1)),
    gen("resample.2_5_complex_default", "resample", {"x": cplx(ctone), "up": 2, "down": 5},
        ctone, 2, 5, default_taps(2, 5)),
    gen("resample.5_3_own_taps", "resample",
        {"x": ramp[:20], "up": 5, "down": 3, "taps": [0.1, -0.2, 0.6, 1.3, 0.6, -0.2, 0.1]},
        ramp[:20], 5, 3, [0.1, -0.2, 0.6, 1.3, 0.6, -0.2, 0.1]),
    {"id": "resample_taps.3_2", "op": "resample_taps", "args": {"up": 3, "down": 2},
     "expected": default_taps(3, 2), "tol": TOL,
     "source": "61 Hamming-windowed taps of 2(1/6) sinc(2(1/6) t), divided by their sum, evaluated "
     "term by term (vectors/generators/resample.py)"},
    {"id": "resample_taps.reduced", "op": "resample_taps", "args": {"up": 4, "down": 6},
     "expected": default_taps(2, 3), "tol": TOL, "source": "4/6 reduces to 2/3, R = 3"},
    err("resample.even_taps", "resample", {"x": [1, 2], "up": 2, "down": 1, "taps": [0.5, 0.5]},
        "resample needs an odd number of taps"),
    err("resample.empty", "resample", {"x": [], "up": 2, "down": 1}, "x must be non-empty"),
    err("resample.up_zero", "resample", {"x": [1], "up": 0, "down": 1}, "up >= 1 required"),
    err("decimate.factor_zero", "decimate", {"x": [1], "factor": 0}, "factor >= 1 required"),
    err("resample.nan_tap", "resample", {"x": [1], "up": 2, "down": 1, "taps": [1, "nan", 1]},
        "taps must be finite"),
    err("resample_taps.one_one", "resample_taps", {"up": 2, "down": 2},
        "2/2 reduces to 1/1, whose cutoff would be fs/2"),
]

doc = {
    "schema": 1,
    "suite": "resample",
    "description": "Rational resampling, interpolation and decimation with the delay removed, and "
    "the default anti-aliasing taps (conventions: Resampling).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "resample.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/resample.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
