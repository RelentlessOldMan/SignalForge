"""Writes vectors/cases/distance_correlation.json, stdlib only.

Distance correlation (conventions: Distance correlation; ADR 0372): the double-centred
distance matrices and the V-statistic sums exact in rationals, then the two square roots in
float.

Run from the repo root: python vectors/generators/distance_correlation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def centred(v):
    n = len(v)
    q = [Fr(u) for u in v]
    a = [[abs(q[i] - q[j]) for j in range(n)] for i in range(n)]
    m = [sum(row, Fr(0)) / n for row in a]
    g = sum(m, Fr(0)) / n
    return [[a[i][j] - m[i] - m[j] + g for j in range(n)] for i in range(n)]


def add(cid, x, y, why):
    n = len(x)
    a, b = centred(x), centred(y)
    nn = n * n
    cov = sum((a[i][j] * b[i][j] for i in range(n) for j in range(n)), Fr(0)) / nn
    va = sum((a[i][j] ** 2 for i in range(n) for j in range(n)), Fr(0)) / nn
    vb = sum((b[i][j] ** 2 for i in range(n) for j in range(n)), Fr(0)) / nn
    assert cov >= 0
    d = math.sqrt(float(cov) / math.sqrt(float(va * vb)))
    cases.append({"id": f"distance_correlation.{cid}", "op": "distance_correlation",
                  "args": {"x": x, "y": y}, "expected": d, "tol": TOL, "source": why})
    return cov, va, vb, d


cov, va, vb, d = add("two_points", [0.0, 1.0], [5.0, 3.0],
                     "N = 2: A = [[-1/2, 1/2], [1/2, -1/2]], B = 2A: dCov^2 = 1/2, dVar^2 "
                     "1/4 and 1: dCor = sqrt((1/2)/sqrt(1/4)) = 1")
assert cov == Fr(1, 2) and va == Fr(1, 4) and vb == 1 and d == 1.0
cov, va, vb, d = add("line", [0.0, 1.0, 2.0, 4.0], [1.0, -1.0, -3.0, -7.0],
                     "y = 1 - 2x: B = 2A exactly, so dCor = 1")
assert cov == 2 * va and vb == 4 * va
cov, va, vb, d = add("square", [-2.0, -1.0, 0.0, 1.0, 2.0], [4.0, 1.0, 0.0, 1.0, 4.0],
                     "y = x^2 on symmetric x: Pearson r is 0, but dCor is not")
assert 0 < d < 1
rng = random.Random(372)
xs = [rng.randint(-24, 24) / 8 for _ in range(40)]
ys = [v * v / 4 + rng.randint(-8, 8) / 8 for v in xs]
add("noisy_parabola", xs, ys,
    "40 random eighths from random.Random(372), y = x^2/4 plus random eighths")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5], "y": [2.0, 1.0, 3.0]}
    base.update(args)
    cases.append({"id": f"distance_correlation.{cid}", "op": "distance_correlation",
                  "args": base, "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0])
err("one_sample", "N must be at least 2", x=[1.0], y=[2.0])
err("constant_x", "x must not be constant", x=[1.0, 1.0, 1.0])
err("constant_y", "y must not be constant", y=[1.0, 1.0, 1.0])
err("nan", "samples must be finite", x=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "distance_correlation",
    "description": "Distance correlation (conventions: Distance correlation; ADR 0372).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "distance_correlation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/distance_correlation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
