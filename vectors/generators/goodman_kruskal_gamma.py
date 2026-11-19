"""Writes vectors/cases/goodman_kruskal_gamma.json, stdlib only.

Goodman and Kruskal's gamma (conventions: Goodman and Kruskal's gamma; ADR 0377): the pairs
counted by brute force.

Run from the repo root: python vectors/generators/goodman_kruskal_gamma.py [--check]
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
    c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            p = sign(Fr(x[i]) - Fr(x[j])) * sign(Fr(y[i]) - Fr(y[j]))
            c += p > 0
            d += p < 0
    g = Fr(c - d, c + d)
    cases.append({"id": f"goodman_kruskal_gamma.{cid}", "op": "goodman_kruskal_gamma",
                  "args": {"x": x, "y": y}, "expected": float(g), "tol": TOL, "source": why})
    return c, d, g


got = add("one_swap", [1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0],
          "of the 6 pairs only (2, 3) is discordant: (5 - 1)/6 = 2/3")
assert got == (5, 1, Fr(2, 3))
got = add("ties_dropped", [1.0, 1.0, 2.0, 3.0], [1.0, 2.0, 2.0, 1.0],
          "pairs (0,1), (0,3), (1,2) tied and dropped; (0,2) concordant; (1,3), (2,3) "
          "discordant: (1 - 2)/3 = -1/3")
assert got == (1, 2, Fr(-1, 3))
got = add("coarse_monotone", [0.0, 0.0, 1.0, 1.0, 2.0, 2.0], [0.0, 0.0, 0.0, 5.0, 5.0, 9.0],
          "every pair untied in both is concordant: gamma = 1 although tau-b is below 1")
assert got[2] == 1
rng = random.Random(377)
xs = [float(rng.randint(0, 4)) for _ in range(50)]
ys = [v + rng.randint(-2, 2) for v in xs]
add("five_levels", xs, ys, "50 random levels 0..4 from random.Random(377), y = x plus "
    "-2..2: heavy ties")
xs = [rng.randint(-64, 64) / 8 for _ in range(40)]
ys = [rng.randint(-64, 64) / 8 for _ in range(40)]
add("independent", xs, ys, "two independent records of 40 random eighths")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5, 2.0, 3.0], "y": [2.0, 1.0, 3.0, 0.0, 1.0]}
    base.update(args)
    cases.append({"id": f"goodman_kruskal_gamma.{cid}", "op": "goodman_kruskal_gamma",
                  "args": base, "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0, 3.0, 4.0])
err("one_sample", "a single sample has no pair", x=[1.0], y=[2.0])
err("constant_x", "every pair is tied in x", x=[1.0, 1.0, 1.0, 1.0, 1.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "goodman_kruskal_gamma",
    "description": "Goodman and Kruskal's gamma (conventions: Goodman and Kruskal's gamma; "
    "ADR 0377).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "goodman_kruskal_gamma.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/goodman_kruskal_gamma.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
