"""Writes vectors/cases/pearson_correlation.json, stdlib only.

Pearson correlation (conventions: Pearson correlation; ADR 0371): dyadic samples with exact
float means (asserted) and sums exact in rationals, then the square root and the quotient in
float.

Run from the repo root: python vectors/generators/pearson_correlation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, y, why):
    n = len(x)
    mx = sum((Fr(v) for v in x), Fr(0)) / n
    my = sum((Fr(v) for v in y), Fr(0)) / n
    assert Fr(math.fsum(x) / n) == mx and Fr(math.fsum(y) / n) == my, cid
    u = [Fr(v) - mx for v in x]
    w = [Fr(v) - my for v in y]
    xy = sum((p * q for p, q in zip(u, w)), Fr(0))
    xx = sum((p * p for p in u), Fr(0))
    yy = sum((q * q for q in w), Fr(0))
    # The sums are exact in float too, so the float product matches the code's order.
    assert all(Fr(float(v)) == v for v in (xy, xx, yy)), cid
    r = float(xy) / math.sqrt(float(xx) * float(yy))
    cases.append({"id": f"pearson_correlation.{cid}", "op": "pearson_correlation",
                  "args": {"x": x, "y": y}, "expected": r, "tol": TOL, "source": why})
    return xy, xx, yy, r


xy, xx, yy, r = add("line", [1.0, 2.0, 3.0, 4.0], [3.0, 5.0, 7.0, 9.0], "y = 2x + 1: r = 1")
assert r == 1.0
xy, xx, yy, r = add("by_hand", [1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0],
                    "deviations -3/2,-1/2,1/2,3/2 and -3/2,1/2,-1/2,3/2: products sum to 4, "
                    "squares to 5 each: r = 4/5")
assert xy == 4 and xx == yy == 5
xy, xx, yy, r = add("not_monotone", [0.0, 1.0, 2.0, 3.0], [0.0, 2.0, 2.0, 0.0],
                    "a tent: deviations -3/2,-1/2,1/2,3/2 and -1,1,1,-1; products sum to 0, so r = 0")
assert xy == 0
rng = random.Random(371)
xs = [rng.randint(-40, 40) / 8 for _ in range(64)]
ys = [0.5 * v + rng.randint(-40, 40) / 8 for v in xs]
add("noisy_pair", xs, ys,
    "64 random eighths from random.Random(371) and half of each plus more random eighths")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5], "y": [2.0, 1.0, 3.0]}
    base.update(args)
    cases.append({"id": f"pearson_correlation.{cid}", "op": "pearson_correlation",
                  "args": base, "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0])
err("one_sample", "N must be at least 2", x=[1.0], y=[2.0])
err("constant_x", "x must not be constant", x=[1.0, 1.0, 1.0])
err("constant_y", "y must not be constant", y=[1.0, 1.0, 1.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "pearson_correlation",
    "description": "Pearson correlation (conventions: Pearson correlation; ADR 0371).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pearson_correlation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pearson_correlation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
