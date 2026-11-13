"""Writes vectors/cases/least_squares.json from the definitions, using only the Python standard
library.

It does not import NumPy or SignalForge. For each design it builds the normal equations from the
conventions' closed-form integrals, checks the integrals against composite Simpson quadrature
(2000 panels per band), and solves the system exactly in rational arithmetic (Fractions of the
float entries), so the taps carry no solver rounding. The hand cases use the orthogonality of the
cosines over [0, fs/2].

Run from the repo root: python vectors/generators/least_squares.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys
from fractions import Fraction

TOL = {"abs": 1e-11, "rel": 1e-10}


def cos_int(u, lo, hi):
    if u == 0:
        return hi - lo
    k = 2 * math.pi * u
    return (math.sin(k * hi) - math.sin(k * lo)) / k


def nu_cos_int(u, lo, hi):
    if u == 0:
        return (hi * hi - lo * lo) / 2
    k = 2 * math.pi * u

    def f(v):
        return v * math.sin(k * v) / k + math.cos(k * v) / (k * k)

    return f(hi) - f(lo)


def simpson(fn, lo, hi, panels=2000):
    step = (hi - lo) / panels
    s = fn(lo) + fn(hi)
    s += 4 * math.fsum(fn(lo + (i + 0.5) * step) for i in range(panels))
    s += 2 * math.fsum(fn(lo + i * step) for i in range(1, panels))
    return s * step / 6


def checked(closed, fn, lo, hi):
    q = simpson(fn, lo, hi)
    assert abs(closed - q) < 1e-11, (closed, q)
    return closed


def solve_exact(g, p):
    """Gauss-Jordan in Fractions: the exact solution of the float system."""
    n = len(p)
    m = [[Fraction(v) for v in row] + [Fraction(p[i])] for i, row in enumerate(g)]
    for col in range(n):
        piv = next(r for r in range(col, n) if m[r][col] != 0)
        m[col], m[piv] = m[piv], m[col]
        inv = 1 / m[col][col]
        m[col] = [v * inv for v in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col]
                m[r] = [a - f * b for a, b in zip(m[r], m[col], strict=True)]
    return [float(m[i][n]) for i in range(n)]


def design(n, bands, desired, fs, weights=None):
    nb = len(bands) // 2
    weights = weights or [1.0] * nb
    odd = n % 2 == 1
    big_l = (n + 1) // 2 if odd else n // 2
    t = [k + (0.0 if odd else 0.5) for k in range(big_l)]
    g = [[0.0] * big_l for _ in range(big_l)]
    p = [0.0] * big_l
    for j in range(nb):
        lo, hi, w = bands[2 * j] / fs, bands[2 * j + 1] / fs, weights[j]
        d0, d1 = desired[2 * j], desired[2 * j + 1]
        slope = (d1 - d0) / (hi - lo)
        for k in range(big_l):
            tk = t[k]
            for m in range(big_l):
                tm = t[m]
                c = (cos_int(tk - tm, lo, hi) + cos_int(tk + tm, lo, hi)) / 2
                if k < 4 and m < 4:  # quadrature check on a corner of G (all of p below)
                    checked(
                        c,
                        lambda v, a=tk, b=tm: math.cos(2 * math.pi * a * v)
                        * math.cos(2 * math.pi * b * v),
                        lo,
                        hi,
                    )
                g[k][m] += w * c
            pk = (d0 - slope * lo) * cos_int(tk, lo, hi) + slope * nu_cos_int(tk, lo, hi)
            checked(
                pk,
                lambda v, a=tk: (d0 + slope * (v - lo)) * math.cos(2 * math.pi * a * v),
                lo,
                hi,
            )
            p[k] += w * pk
    a = solve_exact(g, p)
    h = [0.0] * n
    if odd:
        c = (n - 1) // 2
        h[c] = a[0]
        for k in range(1, big_l):
            h[c + k] = h[c - k] = a[k] / 2
    else:
        for k in range(big_l):
            h[n // 2 + k] = h[n // 2 - 1 - k] = a[k] / 2
    return h


SRC = (
    "vectors/generators/least_squares.py (stdlib only): the conventions' closed-form integrals, "
    "checked against Simpson quadrature, solved exactly in rational arithmetic"
)


def gen(case_id, n, bands, desired, fs, weights=None):
    args = {"num_taps": n, "bands": bands, "desired": desired, "sample_rate": fs}
    if weights is not None:
        args["weights"] = weights
    return {"id": case_id, "op": "fir_least_squares", "args": args,
            "expected": design(n, bands, desired, fs, weights), "tol": TOL, "source": SRC}  # fmt: skip


def hand(case_id, args, expected, why):
    return {"id": case_id, "op": "fir_least_squares", "args": {**args, "sample_rate": 1},
            "expected": expected, "tol": TOL, "source": "by hand: " + why}  # fmt: skip


def err(case_id, args, why):
    base = {"num_taps": 11, "bands": [0, 0.2, 0.3, 0.5], "desired": [1, 1, 0, 0], "sample_rate": 1}
    return {"id": case_id, "op": "fir_least_squares", "args": {**base, **args},
            "error": "invalid_argument", "source": why}  # fmt: skip


cases = [
    hand("fir_least_squares.one_tap_mean", {"num_taps": 1, "bands": [0, 0.2, 0.3, 0.5],
         "desired": [1, 1, 0, 0]}, [0.5],
         "N = 1, A = a0: minimizing int (a0 - D)^2 gives the mean of D over the bands, 0.2/0.4"),
    hand("fir_least_squares.full_band_flat", {"num_taps": 3, "bands": [0, 0.5],
         "desired": [1, 1]}, [0, 1, 0],
         "the cosines are orthogonal over [0, 0.5], so a_k = p_k/G_kk; p_0 = 0.5 = G_00, "
         "p_1 = int cos(2 pi nu) = 0"),
    hand("fir_least_squares.full_band_ramp", {"num_taps": 3, "bands": [0, 0.5],
         "desired": [0, 1]}, [-2 / math.pi**2, 0.5, -2 / math.pi**2],
         "D = 2 nu: a_0 = int 2 nu / 0.5 = 0.5; a_1 = int 2 nu cos(2 pi nu) / (1/4) = "
         "4 (-1/pi^2) (the Fourier series of a triangle wave); h = [a_1/2, a_0, a_1/2]"),
    hand("fir_least_squares.type_2_flat", {"num_taps": 2, "bands": [0, 0.5],
         "desired": [1, 1]}, [2 / math.pi, 2 / math.pi],
         "N = 2, A = b0 cos(pi nu): b0 = int cos(pi nu) / int cos^2(pi nu) = (1/pi)/(1/4), "
         "h = [b0/2, b0/2]"),
    hand("fir_least_squares.weights_scale_cancel", {"num_taps": 3, "bands": [0, 0.5],
         "desired": [0, 1], "weights": [7]}, [-2 / math.pi**2, 0.5, -2 / math.pi**2],
         "one band: its weight scales G and p alike, so full_band_ramp's taps"),
    gen("fir_least_squares.lowpass_31", 31, [0, 0.1, 0.15, 0.5], [1, 1, 0, 0], 1.0),
    gen("fir_least_squares.lowpass_30_even", 30, [0, 0.1, 0.15, 0.5], [1, 1, 0, 0], 1.0),
    gen("fir_least_squares.bandpass_weighted_hz", 41, [0, 800, 1200, 2000, 2400, 4000],
        [0, 0, 1, 1, 0, 0], 8000.0, [10, 1, 10]),
    gen("fir_least_squares.sloped_band", 25, [0, 0.3, 0.35, 0.5], [0.2, 1.4, 0, 0], 1.0, [1, 3]),
    gen("fir_least_squares.highpass_odd", 21, [0, 0.2, 0.3, 0.5], [0, 0, 1, 1], 1.0),
    gen("fir_least_squares.even_with_gain_at_nyquist", 16, [0, 0.2, 0.3, 0.5], [0, 0, 1, 1], 1.0),
    gen("fir_least_squares.long_101", 101, [0, 0.2, 0.22, 0.5], [1, 1, 0, 0], 1.0, [1, 5]),
    err("fir_least_squares.zero_taps", {"num_taps": 0}, "1 <= num_taps"),
    err("fir_least_squares.too_many_taps", {"num_taps": 1002}, "num_taps <= 1001"),
    err("fir_least_squares.one_value_per_band", {"desired": [1, 0]}, "two desired values per band"),
    err("fir_least_squares.odd_band_edges", {"bands": [0, 0.2, 0.3]}, "bands come in pairs"),
    err("fir_least_squares.edges_not_increasing", {"bands": [0, 0.2, 0.2, 0.5]},
        "edges must increase strictly"),
    err("fir_least_squares.edge_above_nyquist", {"bands": [0, 0.2, 0.3, 0.6]},
        "edges <= sample_rate/2"),
    err("fir_least_squares.zero_weight", {"weights": [1, 0]}, "weights must be positive"),
    err("fir_least_squares.nan_desired", {"desired": [1, "nan", 0, 0]}, "desired must be finite"),
    err("fir_least_squares.zero_rate", {"sample_rate": 0}, "sample_rate must be > 0"),
]  # fmt: skip

# The hand values are also what the generator's design gives.
for c in cases[:5]:
    a = c["args"]
    got = design(a["num_taps"], a["bands"], a["desired"], a["sample_rate"], a.get("weights"))
    assert all(abs(x - y) < 1e-14 for x, y in zip(got, c["expected"], strict=True)), c["id"]

doc = {
    "schema": 1,
    "suite": "least_squares",
    "description": "Least-squares FIR design: exact weighted integral squared error, the desired "
    "gain linear across each band (conventions: FIR filters, Least-squares design).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "least_squares.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/least_squares.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
