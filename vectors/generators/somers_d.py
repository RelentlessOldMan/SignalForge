"""Writes vectors/cases/somers_d.json, stdlib only.

Somers' D (conventions: Somers' D; ADR 0378): the pairs counted by brute force.

Run from the repo root: python vectors/generators/somers_d.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def sign(v):
    return (v > 0) - (v < 0)


def add(cid, x, y, why):
    n = len(x)
    c = d = tx = 0
    for i in range(n):
        for j in range(i + 1, n):
            sx = sign(Fr(x[i]) - Fr(x[j]))
            p = sx * sign(Fr(y[i]) - Fr(y[j]))
            c += p > 0
            d += p < 0
            tx += sx == 0
    v = Fr(c - d, n * (n - 1) // 2 - tx)
    cases.append({"id": f"somers_d.{cid}", "op": "somers_d", "args": {"x": x, "y": y},
                  "expected": float(v), "tol": TOL, "source": why})
    return c, d, tx, v


got = add("one_swap", [1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0],
          "no ties: 5 concordant, 1 discordant of 6 pairs: 4/6 = 2/3, Kendall's tau")
assert got == (5, 1, 0, Fr(2, 3))
got = add("ties_yx", [1.0, 1.0, 2.0, 3.0], [1.0, 2.0, 2.0, 1.0],
          "C = 1, D = 2; one pair tied in x: (1 - 2)/(6 - 1) = -1/5")
assert got == (1, 2, 1, Fr(-1, 5))
got = add("ties_xy", [1.0, 2.0, 2.0, 1.0], [1.0, 1.0, 2.0, 3.0],
          "the same records swapped: two pairs tied in the predictor: (1 - 2)/(6 - 2) = -1/4")
assert got == (1, 2, 2, Fr(-1, 4))
rng = random.Random(378)
xs = [float(rng.randint(0, 3)) for _ in range(50)]
ys = [v * 2 + rng.randint(-3, 3) / 4 for v in xs]
add("coarse_predictor", xs, ys, "50 random levels 0..3 from random.Random(378), y = 2x "
    "plus random quarters: many ties in x")
xs = [rng.randint(-64, 64) / 8 for _ in range(40)]
ys = [rng.randint(-8, 8) / 2 for _ in range(40)]
add("independent", xs, ys, "two independent records of 40 random eighths and halves")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5, 2.0, 3.0], "y": [2.0, 1.0, 3.0, 0.0, 1.0]}
    base.update(args)
    cases.append({"id": f"somers_d.{cid}", "op": "somers_d", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0, 3.0, 4.0])
err("one_sample", "a single sample has no pair", x=[1.0], y=[2.0])
err("constant_x", "every pair is tied in x", x=[1.0, 1.0, 1.0, 1.0, 1.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "somers_d",
    "description": "Somers' D (conventions: Somers' D; ADR 0378).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "somers_d.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/somers_d.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
