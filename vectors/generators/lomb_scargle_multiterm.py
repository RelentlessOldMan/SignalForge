"""Writes vectors/cases/lomb_scargle_multiterm.json from first principles, using only the Python
standard library.

It does not import NumPy or SignalForge, and it uses neither centering nor Gram-Schmidt. At each
frequency it builds the uncentered design 1, cos(k w t), sin(k w t) for k = 1 ... terms from the
floating-point values of math.cos and math.sin, and solves the weighted normal equations in exact
rational arithmetic (fractions.Fraction). chi2 is the weighted residual of that fit and chi2_0 the
weighted scatter about the weighted mean; the standard value is (chi2_0 - chi2)/chi2_0 and the
power half the drop (conventions: Spectra, Multiterm Lomb-Scargle; ADR 0103). A square wave on
eight even samples is worked by hand from its DFT.

Run from the repo root: python vectors/generators/lomb_scargle_multiterm.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction

cases = []
TOL = {"abs": 1e-12, "rel": 1e-9}
SRC = ("vectors/generators/lomb_scargle_multiterm.py (stdlib only): weighted normal equations of "
       "the uncentered harmonic model solved in exact rationals at each frequency")
OP = "lomb_scargle_multiterm"


def add(cid, args, expected, source=SRC, tol=TOL):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": args, "expected": expected, "tol": tol,
                  "source": source})


def err(cid, args, source):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": args, "error": "invalid_argument",
                  "source": source})


def solve(a, b):
    """Gauss-Jordan elimination in exact rationals; fails on a singular matrix."""
    n = len(b)
    m = [row[:] + [v] for row, v in zip(a, b)]
    for c in range(n):
        p = next(r for r in range(c, n) if m[r][c] != 0)
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c and m[r][c] != 0:
                q = m[r][c] / m[c][c]
                m[r] = [x - q * z for x, z in zip(m[r], m[c])]
    return [m[r][n] / m[r][r] for r in range(n)]


def periodogram(t, y, freqs, terms, sigma=None, normalization="standard"):
    w = [Fraction(1) / (Fraction(s) * Fraction(s)) for s in sigma] if sigma else [Fraction(1)] * len(t)
    yf = [Fraction(v) for v in y]
    big_w = sum(w)
    mean = sum(wi * v for wi, v in zip(w, yf)) / big_w
    chi0 = sum(wi * (v - mean) ** 2 for wi, v in zip(w, yf))
    out = []
    for f in freqs:
        om = 2 * math.pi * f
        cols = [[Fraction(1)] * len(t)]
        for k in range(1, terms + 1):
            cols.append([Fraction(math.cos(om * k * v)) for v in t])
            cols.append([Fraction(math.sin(om * k * v)) for v in t])
        a = [[sum(wi * x * z for wi, x, z in zip(w, ci, cj)) for cj in cols] for ci in cols]
        b = [sum(wi * x * v for wi, x, v in zip(w, ci, yf)) for ci in cols]
        beta = solve(a, b)
        fit = [sum(bj * cj[n] for bj, cj in zip(beta, cols)) for n in range(len(t))]
        chi = sum(wi * (v - u) ** 2 for wi, v, u in zip(w, yf, fit))
        drop = chi0 - chi
        out.append(float(drop / chi0) if normalization == "standard" else float(drop / 2))
    return out


def case(cid, t, y, freqs, terms, sigma=None, normalization=None):
    args = {"times": t, "values": y, "frequencies": freqs, "terms": terms}
    if sigma is not None:
        args["uncertainties"] = sigma
    if normalization is not None:
        args["normalization"] = normalization
    add(cid, args, periodogram(t, y, freqs, terms, sigma, normalization or "standard"))


rng = random.Random(103)
t1 = sorted(round(rng.uniform(0, 20), 6) for _ in range(30))
noise = [round(rng.gauss(0, 1), 6) for _ in t1]
grid = [0.07, 0.19, 0.33, 0.52, 0.81]
case("noise_one_term", t1, noise, grid, 1)
case("noise_two_terms", t1, noise, grid, 2)
saw = [round(((0.37 * v) % 1) - 0.5 + 0.05 * rng.gauss(0, 1), 6) for v in t1]
case("sawtooth_four_terms", t1, saw, [0.185, 0.37, 0.74], 4)
sig = [round(rng.uniform(0.5, 2.0), 6) for _ in t1]
case("weighted_three_terms", t1, saw, [0.37, 0.41], 3, sigma=sig)
case("weighted_three_terms_power", t1, saw, [0.37, 0.41], 3, sigma=sig, normalization="power")
t2 = sorted(round(rng.uniform(-3, 5), 6) for _ in range(12))
y2 = [round(2 + math.cos(2 * math.pi * 0.6 * v) - 0.4 * math.sin(4 * math.pi * 0.6 * v), 6)
      for v in t2]
case("two_harmonics_two_terms", t2, y2, [0.6, 0.9], 2)
case("two_harmonics_power", t2, y2, [0.6], 2, normalization="power")

# By hand (ADR 0103): the square wave on t = 0 ... 7 at f = 1/8. Its DFT has |X1|^2 = 4/sin^2(pi/8)
# and |X3|^2 = 4/sin^2(3 pi/8) out of 64, nothing at even bins; terms = 1 and 2 explain
# 2|X1|^2/64 = (1 + sqrt(2)/2)/2, terms = 3 everything, terms = 4 drops the Nyquist sine.
sq_t, sq_y = [float(n) for n in range(8)], [1.0] * 4 + [-1.0] * 4
part = (1 + math.sqrt(2) / 2) / 2
assert abs(2 * (4 / math.sin(math.pi / 8) ** 2) / 64 - part) < 1e-15
assert abs(2 * (4 / math.sin(3 * math.pi / 8) ** 2) / 64 - (1 - part)) < 1e-15
by_hand = "by hand: the square wave's DFT on eight samples (ADR 0103)"
for terms, want in ((1, part), (2, part), (3, 1.0), (4, 1.0)):
    add(f"square_terms{terms}_by_hand",
        {"times": sq_t, "values": sq_y, "frequencies": [0.125], "terms": terms}, [want], by_hand)
add("square_power_by_hand", {"times": sq_t, "values": sq_y, "frequencies": [0.125], "terms": 3,
    "normalization": "power"}, [4.0], "by hand: an exact fit explains half of sum y^2 = 8")
add("empty_frequencies", {"times": sq_t, "values": sq_y, "frequencies": [], "terms": 2}, [],
    "by hand: no frequencies, no values")

base = {"times": [0.0, 0.4, 1.1, 2.0], "values": [1.0, -0.5, 0.25, 2.0], "frequencies": [0.3],
        "terms": 2}
for cid, change, why in (
    ("zero_terms", {"terms": 0}, "terms must be at least 1"),
    ("constant_standard", {"values": [3.0] * 4}, "the standard normalization needs scatter"),
    ("zero_frequency", {"frequencies": [0.0]}, "frequencies must be positive"),
    ("nan_time", {"times": [0.0, "nan", 1.1, 2.0]}, "times must be finite"),
    ("length_mismatch", {"values": [1.0, 2.0, 3.0]}, "times and values differ in length"),
    ("one_sample", {"times": [0.0], "values": [1.0]}, "at least two samples"),
    ("zero_uncertainty", {"uncertainties": [1.0, 0.0, 1.0, 1.0]}, "uncertainties must be > 0"),
    ("short_uncertainties", {"uncertainties": [1.0, 1.0]}, "one uncertainty per sample"),
    ("bad_normalization", {"normalization": "psd"}, "normalization is standard or power"),
):
    err(cid, base | change, why)

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Multiterm Lomb-Scargle periodogram (conventions: Spectra, Multiterm "
    "Lomb-Scargle; ADR 0103).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{OP}.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/{OP}.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
