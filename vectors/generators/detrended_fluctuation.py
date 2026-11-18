"""Writes vectors/cases/detrended_fluctuation.json, stdlib only.

Detrended fluctuation analysis, DFA-1 (conventions: Detrended fluctuation analysis; ADR 0332):
the profile Y[i] = sum_{j<=i} (x[j] - mean), each box's least-squares line and each F(s)^2 =
sum r^2 / (B s) exact in rationals from dyadic samples; then sqrt, ln and the least-squares
slope of ln F against ln s in float.

Run from the repo root: python vectors/generators/detrended_fluctuation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def f_squared(x, s):
    q = [Fr(v) for v in x]
    mean = sum(q, Fr(0)) / len(q)
    profile, run = [], Fr(0)
    for v in q:
        run += v - mean
        profile.append(run)
    boxes = len(q) // s
    tm = Fr(s - 1, 2)
    stt = sum(((t - tm) ** 2 for t in range(s)), Fr(0))
    total = Fr(0)
    for b in range(boxes):
        y = profile[b * s:(b + 1) * s]
        ym = sum(y, Fr(0)) / s
        slope = sum(((t - tm) * (y[t] - ym) for t in range(s)), Fr(0)) / stt
        total += sum(((y[t] - ym - slope * (t - tm)) ** 2 for t in range(s)), Fr(0))
    return total / (boxes * s)


def add(cid, x, scales, why):
    f2 = [f_squared(x, s) for s in scales]
    lx = [math.log(s) for s in scales]
    ly = [0.5 * math.log(v) for v in f2]
    mx, my = math.fsum(lx) / len(lx), math.fsum(ly) / len(ly)
    alpha = (math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly))
             / math.fsum((a - mx) ** 2 for a in lx))
    cases.append({"id": f"detrended_fluctuation.{cid}", "op": "detrended_fluctuation",
                  "args": {"samples": x, "scales": scales},
                  "expected": {"scales": scales, "fluctuations": [math.sqrt(v) for v in f2],
                               "alpha": alpha},
                  "tol": TOL, "source": why})
    return f2


f2 = add("alternating", [1.0, -1.0] * 4, [4, 8], "+-1 alternating: profile 1, 0, 1, 0, ...; "
         "at s = 4 the residuals are 0.2, -0.6, 0.6, -0.2, F^2 = 1/5")
assert f2[0] == Fr(1, 5), f2
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0, 1.25, 0.625, -2.0, 0.25, 1.75], [4, 5, 7, 11, 23],
    "23 arbitrary dyadic samples, leftovers at the end of most scales")
add("walk", [float(v) for v in (0, 1, 3, 2, 4, 5, 3, 6, 8, 7, 9, 12, 10, 11, 14, 13)], [4, 8, 16],
    "an integer walk with drift, one box at s = 16")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 3.0, -1.0, 0.25], "scales": [4, 8]}
    base.update(args)
    cases.append({"id": f"detrended_fluctuation.{cid}", "op": "detrended_fluctuation",
                  "args": base, "error": "invalid_argument", "source": why})


err("one_scale", "at least two scales are needed", scales=[4])
err("scale_three", "each scale must be at least 4", scales=[3, 4])
err("scale_too_big", "each scale must be at most N", scales=[4, 9])
err("not_increasing", "scales must be strictly increasing", scales=[8, 4])
err("constant", "a constant has a zero profile", samples=[2.5] * 8)
err("nan", "samples must be finite", samples=[0.0, 1.0, "nan", 2.0, 1.0, 0.0, 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "detrended_fluctuation",
    "description": "Detrended fluctuation analysis, DFA-1 (conventions: Detrended fluctuation "
                   "analysis; ADR 0332).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "detrended_fluctuation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/detrended_fluctuation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
