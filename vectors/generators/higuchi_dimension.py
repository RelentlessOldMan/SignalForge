"""Writes vectors/cases/higuchi_dimension.json, stdlib only.

Higuchi fractal dimension (conventions: Higuchi fractal dimension; ADR 0330): each L(k) exact
in rationals from dyadic samples, L_m(k) = sum |x[m+ik] - x[m+(i-1)k]| (N-1) / (n_m k) / k
averaged over m < k; then the least-squares slope of ln L(k) against -ln k in float.

Run from the repo root: python vectors/generators/higuchi_dimension.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def dimension(x, kmax):
    q = [Fr(v) for v in x]
    size = len(q)
    lx, ly = [], []
    for k in range(1, kmax + 1):
        total = Fr(0)
        for m in range(k):
            steps = (size - 1 - m) // k
            s = sum((abs(q[m + i * k] - q[m + (i - 1) * k]) for i in range(1, steps + 1)), Fr(0))
            total += s * (size - 1) / (steps * k) / k
        lx.append(-math.log(k))
        ly.append(math.log(total / k))
    mx, my = math.fsum(lx) / kmax, math.fsum(ly) / kmax
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly))
    sxx = math.fsum((a - mx) ** 2 for a in lx)
    return sxy / sxx


def add(cid, x, kmax, why):
    d = dimension(x, kmax)
    cases.append({"id": f"higuchi_dimension.{cid}", "op": "higuchi_dimension",
                  "args": {"samples": x, "k_max": kmax}, "expected": d, "tol": TOL,
                  "source": why})
    return d


d = add("line", [0.5 * i - 2.0 for i in range(20)], 6, "a straight line: L(k) = (N-1)/k, "
        "dimension 1")
assert abs(d - 1) < 1e-14, d
add("zigzag_three", [1.0, -1.0, 0.5, -0.5] * 5, 3, "a period-4 zigzag, k = 1, 2, 3")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0, 1.25, 0.625], 5, "twenty arbitrary dyadic samples")
add("tight", [0.0, 1.0, 3.0, 2.0, 5.0, 4.0], 3, "six samples, k_max 3: 2 k_max = N, the "
    "last start has one step")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 3.0], "k_max": 2}
    base.update(args)
    cases.append({"id": f"higuchi_dimension.{cid}", "op": "higuchi_dimension", "args": base,
                  "error": "invalid_argument", "source": why})


err("k_one", "k_max must be at least 2", k_max=1)
err("k_too_big", "2 k_max must be at most N", k_max=4)
err("constant", "a constant has no curve length", samples=[2.0] * 6)
err("flat_at_two", "+-1 alternating: at k = 2 both starts are flat, so L(2) = 0",
    samples=[1.0, -1.0] * 4)
err("inf", "samples must be finite", samples=[0.0, 1.0, "-inf", 2.0])

doc = {
    "schema": 1,
    "suite": "higuchi_dimension",
    "description": "Higuchi fractal dimension (conventions: Higuchi fractal dimension; ADR 0330).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "higuchi_dimension.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/higuchi_dimension.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
