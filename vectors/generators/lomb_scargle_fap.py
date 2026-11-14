"""Writes vectors/cases/lomb_scargle_fap.json from first principles, using only the Python standard
library.

It does not import NumPy or SignalForge.

- False alarm: P1 = (1 - z)^((N - d)/2), d = 3 centered and 2 not, then 1 - (1 - P1)^M. When the
  exponent is whole, z is a short decimal and the whole expression is computed exactly with
  fractions.Fraction, then rounded once to a float; a half exponent uses math.sqrt of an exact
  fraction (M = 1 only).
- Frequency grid: k / (oversampling * T) for k = 1 .. K with K counted by hand from f_max * T *
  oversampling, which the cases choose so the count is clear (whole or well away from whole).

Run from the repo root: python vectors/generators/lomb_scargle_fap.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys
from fractions import Fraction

cases = []
TOL = {"abs": 0, "rel": 1e-12}  # relative only: some values are 1e-97


def add(op, cid, args, expected, source):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "expected": expected, "tol": TOL,
                  "source": source})


def err(op, cid, args, source):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": source})


def fap_exact(z, n, m, center):
    """Exact 1 - (1 - (1 - z)^e)^m for a whole e = (n - d)/2, z given as a decimal string."""
    d = 3 if center else 2
    assert (n - d) % 2 == 0
    p1 = (1 - Fraction(z)) ** ((n - d) // 2)
    return float(1 - (1 - p1) ** m)


FA = "lomb_scargle_false_alarm"
for cid, z, n, m, center in [
    ("half_n13", "0.5", 13, 1, True),          # (1/2)^5
    ("half_n13_m10", "0.5", 13, 10, True),
    ("n12_uncentered", "0.5", 12, 1, False),   # (1/2)^5, d = 2
    ("small_z", "0.01", 101, 1, True),         # 0.99^49
    ("tiny_p1_many", "0.9", 203, 1000, True),  # 0.1^100: 1 - (1 - p)^M needs log1p/expm1
    ("tiny_p1_one", "0.9", 203, 1, True),
    ("mid_m200", "0.2", 43, 200, True),        # 0.8^20 over 200 frequencies
    ("zero_power", "0", 13, 7, True),          # P1 = 1, so 1
    ("unit_power", "1", 13, 5, True),          # P1 = 0, so 0
    ("min_n_centered", "0.3", 5, 1, True),     # e = 1: 0.7
    ("min_n_uncentered", "0.3", 4, 3, False),  # e = 1: 1 - 0.3^3
]:
    args = {"power": float(z), "num_samples": n}
    if m != 1:
        args["num_frequencies"] = m
    if not center:
        args["center"] = False
    d = 3 if center else 2
    add(FA, cid, args, fap_exact(z, n, m, center),
        f"exact fractions: 1 - (1 - (1 - {z})^{(n - d) // 2})^{m}")

# Half exponents, M = 1: (1 - z)^(e/2) = sqrt((1 - z)^e).
add(FA, "half_exponent", {"power": 0.75, "num_samples": 4}, math.sqrt(0.25),
    "N = 4 centered: (1 - 0.75)^(1/2) = 0.5")
add(FA, "half_exponent_n10", {"power": 0.36, "num_samples": 10},
    math.sqrt(float(Fraction(16, 25) ** 7)), "N = 10 centered: 0.64^(7/2) = 0.8^7")

err(FA, "power_above_one", {"power": 1.5, "num_samples": 10}, "z must be in [0, 1]")
err(FA, "power_negative", {"power": -0.1, "num_samples": 10}, "z must be in [0, 1]")
err(FA, "power_nan", {"power": "nan", "num_samples": 10}, "z must be in [0, 1]")
err(FA, "n_too_small_centered", {"power": 0.5, "num_samples": 3}, "N >= 4 when centered")
err(FA, "n_too_small_uncentered", {"power": 0.5, "num_samples": 2, "center": False},
    "N >= 3 when not centered")
err(FA, "zero_frequencies", {"power": 0.5, "num_samples": 10, "num_frequencies": 0}, "M >= 1")

FR = "lomb_scargle_frequencies"
add(FR, "default", {"times": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
    [k / 50 for k in range(1, 28)],
    "T = 10, df = 1/50, f_max = 11/20 = 27.5 df: k = 1..27")
add(FR, "oversampling_1", {"times": [3, 0.5, 2.5], "oversampling": 1},
    [k / 2.5 for k in range(1, 2)], "T = 2.5, df = 0.4, f_max = 3/5 = 1.5 df: k = 1")
add(FR, "max_frequency", {"times": [0, 0.3, 1.7, 4], "oversampling": 2, "max_frequency": 1},
    [k / 8 for k in range(1, 9)], "T = 4, df = 1/8, f_max = 1 = 8 df exactly: k = 1..8")
add(FR, "unsorted_negative", {"times": [1, -1, 0.25], "oversampling": 4, "max_frequency": 0.9},
    [k / 8 for k in range(1, 8)], "T = 2, df = 1/8, f_max = 7.2 df: k = 1..7")
add(FR, "empty", {"times": [0, 1], "oversampling": 1, "max_frequency": 0.5}, [],
    "T = 1, df = 1, f_max = 0.5 df: no frequencies")
err(FR, "one_time", {"times": [1]}, "at least 2 times")
err(FR, "equal_times", {"times": [2, 2, 2]}, "T = 0")
err(FR, "inf_time", {"times": [0, "inf"]}, "times must be finite")
err(FR, "zero_oversampling", {"times": [0, 1], "oversampling": 0}, "oversampling > 0")
err(FR, "negative_max", {"times": [0, 1], "max_frequency": -1}, "f_max > 0")
err(FR, "too_many", {"times": [0, 1], "oversampling": 1e6, "max_frequency": 100},
    "K = 10^8 > 10^7")

doc = {
    "schema": 1,
    "suite": "lomb_scargle_fap",
    "description": "Lomb-Scargle false-alarm probability and frequency grid (conventions: Spectra, "
    "Lomb-Scargle false-alarm probability and frequency grid; ADR 0062).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lomb_scargle_fap.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, float | int) and isinstance(b, float | int) and not isinstance(a, bool):
        return a == b or abs(a - b) <= 1e-14 * max(abs(a), abs(b))
    return a == b


def render(d):
    head = json.dumps({k: v for k, v in d.items() if k != "cases"}, indent=2)[:-2]
    body = ",\n".join("    " + json.dumps(c) for c in d["cases"])
    return head + ',\n  "cases": [\n' + body + "\n  ]\n}\n"


if "--check" in sys.argv:
    if not out.exists() or not same(json.loads(out.read_text(encoding="utf-8")), doc):
        print(f"{out.name} is out of date: run python vectors/generators/lomb_scargle_fap.py")
        sys.exit(1)
    print(f"{out.name} matches")
else:
    out.write_text(render(doc), encoding="utf-8", newline="\n")
    print(f"wrote {out.name}: {len(cases)} cases")
