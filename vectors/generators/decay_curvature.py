"""Writes vectors/cases/decay_curvature.json, stdlib only.

Decay curvature (conventions: Decay curvature; ADR 0182): C = 100 (T30/T20 - 1) with T20 fitted
from -5 to -25 dB and T30 from -5 to -35 dB of the Schroeder decay. For h[n] = sum_j c_j r_j^n
over N samples the tail is the exact geometric sum of every cross term; the curve and both
least-squares slopes are worked in 50-digit decimal, with every curve value kept at least
1e-6 dB from the fit levels.

Run from the repo root: python vectors/generators/decay_curvature.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-9, "rel": 1e-11}
cases = []


def curve(parts, length):
    energy = []
    for n in range(length):
        e = D(0)
        for ci, ri in parts:
            for cj, rj in parts:
                q = D(ri) * D(rj)
                e += D(ci) * D(cj) * (q ** n - q ** length) / (1 - q)
        energy.append(e)
    d = [(e / energy[0]).log10() * 10 if e > 0 else None for e in energy]
    for v in d:
        for level in (-5, -25, -35):
            assert v is None or abs(v - level) > D("1e-6"), v
    return d


def fit(d, fs, a, b):
    n1 = next(i for i, v in enumerate(d) if v is not None and v <= a)
    n2 = next(i for i, v in enumerate(d) if v is not None and v <= b)
    ns = range(n1, n2)
    mn = D(sum(ns)) / len(ns)
    my = sum(d[n] for n in ns) / len(ns)
    return -60 / (sum((n - mn) * (d[n] - my) for n in ns) / sum((n - mn) ** 2 for n in ns) * D(fs))


def add(cid, parts, length, fs, why, turn=None, near_zero=False):
    d = curve(parts, length)
    c = 100 * (fit(d, fs, -5, -35) / fit(d, fs, -5, -25) - 1)
    if near_zero:
        assert abs(c) < D("1e-12"), (cid, c)
    else:
        assert c > 1, (cid, c)
    x = [sum(ci * r ** n for ci, r in parts) for n in range(length)]
    if turn is None:
        ir = x
    else:
        ir = {"re": [v * math.cos(turn * n) for n, v in enumerate(x)],
              "im": [v * math.sin(turn * n) for n, v in enumerate(x)]}
    cases.append({"id": f"decay_curvature.{cid}", "op": "decay_curvature",
                  "args": {"impulse_response": ir, "sample_rate": fs},
                  "expected": float(c), "tol": TOL, "source": why})


add("single", [(1.0, 0.99)], 3000, 1000.0,
    "h = 0.99^n over 3000 samples: the exact tail is a straight line to 1e-26 dB, so C = 0",
    near_zero=True)
add("two_slope", [(1.0, 0.98), (0.05, 0.995)], 3000, 1000.0,
    "a fast decay plus a weak slow one: the exact tail of the sum with its cross term bends "
    "toward the slow slope, so T30 > T20")
add("complex", [(1.0, 0.98), (0.05, 0.995)], 3000, 1000.0,
    "the two-slope response times e^(0.7jn): |h| unchanged, same C", turn=0.7)


def err(cid, ir, fs, why):
    cases.append({"id": f"decay_curvature.{cid}", "op": "decay_curvature",
                  "args": {"impulse_response": ir, "sample_rate": fs},
                  "error": "invalid_argument", "source": why})


err("short_of_35", [0.9 ** n for n in range(25)], 1000.0,
    "0.9^n over 25 samples: the last tail is 0.81^24 (1 - 0.81) / (1 - 0.81^25) of the total, "
    "about -29 dB, so T30 never reaches -35 dB")
err("silent", [0.0, 0.0, 0.0], 1000.0, "all zero")
err("zero_rate", [0.9 ** n for n in range(200)], 0.0, "sample_rate must be positive")
err("nan", [1.0, "nan", 0.5], 1000.0, "not finite")

doc = {
    "schema": 1,
    "suite": "decay_curvature",
    "description": "Decay curvature (conventions: Decay curvature; ADR 0182).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "decay_curvature.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/decay_curvature.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
