"""Writes vectors/cases/hoeffding_d.json, stdlib only.

Hoeffding's D (conventions: Hoeffding's D; ADR 0374): mean ranks, bivariate ranks with the
1/2 tie rule, and the three sums exact in rationals.

Run from the repo root: python vectors/generators/hoeffding_d.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def ranks(v):
    return [sum(1 for u in v if u < w) + Fr(sum(1 for u in v if u == w) + 1, 2) for w in v]


def phi(a, b):
    return Fr(1) if a < b else Fr(1, 2) if a == b else Fr(0)


def add(cid, x, y, why):
    n = len(x)
    r, s = ranks(x), ranks(y)
    q = [1 + sum((phi(x[j], x[i]) * phi(y[j], y[i]) for j in range(n) if j != i), Fr(0))
         for i in range(n)]
    d1 = sum(((v - 1) * (v - 2) for v in q), Fr(0))
    d2 = sum(((a - 1) * (a - 2) * (b - 1) * (b - 2) for a, b in zip(r, s)), Fr(0))
    d3 = sum(((a - 2) * (b - 2) * (v - 1) for a, b, v in zip(r, s, q)), Fr(0))
    d = Fr(30) * ((n - 2) * (n - 3) * d1 + d2 - 2 * (n - 2) * d3) / (
        n * (n - 1) * (n - 2) * (n - 3) * (n - 4))
    cases.append({"id": f"hoeffding_d.{cid}", "op": "hoeffding_d", "args": {"x": x, "y": y},
                  "expected": float(d), "tol": TOL, "source": why})
    return d1, d2, d3, d


d1, d2, d3, d = add("monotone_five", [1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 8.0, 16.0, 32.0],
                    "R = S = Q = 1..5: D1 = 20, D2 = 184, D3 = 50; 30(6*20 + 184 - 300)/120 "
                    "= 1")
assert (d1, d2, d3, d) == (20, 184, 50, 1)
d1, d2, d3, d = add("reversed_five", [1.0, 2.0, 3.0, 4.0, 5.0], [5.0, 4.0, 3.0, 2.0, 1.0],
                    "S = 6 - R and every Q = 1: D1 = 0, D3 = 0; D2 has one nonzero term, "
                    "R = S = 3: 2*1*2*1 = 4; 30*4/120 = 1, complete dependence")
assert (d1, d2, d3, d) == (0, 4, 0, 1)
rng = random.Random(374)
xs = [float(rng.randint(-6, 6)) for _ in range(30)]
ys = [abs(v) + rng.randint(-1, 1) for v in xs]
add("v_shape_with_ties", xs, ys,
    "30 random integers from random.Random(374), y = |x| plus -1, 0 or 1: not monotone, "
    "with ties in both")
xs = [rng.randint(-64, 64) / 8 for _ in range(40)]
ys = [rng.randint(-64, 64) / 8 for _ in range(40)]
add("independent", xs, ys, "two independent records of 40 random eighths")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5, 2.0, 3.0], "y": [2.0, 1.0, 3.0, 0.0, 1.0]}
    base.update(args)
    cases.append({"id": f"hoeffding_d.{cid}", "op": "hoeffding_d", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0, 3.0, 4.0])
err("four_samples", "N must be at least 5", x=[1.0, 2.0, 3.0, 4.0], y=[1.0, 2.0, 3.0, 4.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "hoeffding_d",
    "description": "Hoeffding's D (conventions: Hoeffding's D; ADR 0374).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hoeffding_d.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hoeffding_d.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
