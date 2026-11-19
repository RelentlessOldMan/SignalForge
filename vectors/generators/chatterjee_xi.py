"""Writes vectors/cases/chatterjee_xi.json, stdlib only.

Chatterjee's xi (conventions: Chatterjee's xi; ADR 0376): a stable sort by x and the counts
r and l by brute force, in integers.

Run from the repo root: python vectors/generators/chatterjee_xi.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, x, y, why):
    n = len(x)
    order = sorted(range(n), key=lambda i: (x[i], i))
    ys = [y[i] for i in order]
    r = [sum(1 for u in y if u <= v) for v in ys]
    left = [sum(1 for u in y if u >= v) for v in ys]
    s = sum(abs(r[i + 1] - r[i]) for i in range(n - 1))
    t = sum(v * (n - v) for v in left)
    xi = 1 - Fr(n * s, 2 * t)
    cases.append({"id": f"chatterjee_xi.{cid}", "op": "chatterjee_xi",
                  "args": {"x": x, "y": y}, "expected": float(xi), "tol": TOL, "source": why})
    return s, t, xi


got = add("monotone_five", [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0],
          "r = 1..5, S = 4; l = 5..1, T = 0 + 4 + 6 + 6 + 4 = 20; 1 - 5*4/40 = 1/2 "
          "= 1 - 3/(N + 1)")
assert got == (4, 20, Fr(1, 2))
got = add("v_shape", [-2.0, -1.0, 0.0, 1.0, 2.0], [4.0, 1.0, 0.0, 1.0, 4.0],
          "y = x^2: r in x order 5, 3, 1, 3, 5, S = 8; l = 2, 4, 5, 4, 2, "
          "T = 6 + 4 + 0 + 4 + 6 = 20; 1 - 5*8/40 = 0")
assert got == (8, 20, 0)
got = add("ties_in_x_record_order", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 3.0, 2.0],
          "stable order by x: indices 1, 3, 0, 2, y = 1, 2, 0, 3; r = 2, 3, 1, 4, S = 6; "
          "l = 3, 2, 4, 1, T = 3 + 4 + 0 + 3 = 10; 1 - 4*6/20 = -1/5 (order 1, 3, 2, 0 "
          "would give S = 5)")
assert got == (6, 10, Fr(-1, 5))
rng = random.Random(376)
xs = [rng.randint(-40, 40) / 8 for _ in range(60)]
ys = [v * v + rng.randint(-8, 8) / 8 for v in xs]
add("parabola_with_ties", xs, ys,
    "60 random eighths from random.Random(376), y = x^2 plus random eighths: ties in both")
xs = [rng.random() for _ in range(45)]
ys = [rng.random() for _ in range(45)]
add("independent", xs, ys, "two independent records of 45 uniform values")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5, 2.0, 3.0], "y": [2.0, 1.0, 3.0, 0.0, 1.0]}
    base.update(args)
    cases.append({"id": f"chatterjee_xi.{cid}", "op": "chatterjee_xi", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0, 3.0, 4.0])
err("one_sample", "N must be at least 2", x=[1.0], y=[2.0])
err("constant_y", "the denominator is 0 when y is constant", y=[1.0, 1.0, 1.0, 1.0, 1.0])
err("nan", "samples must be finite", x=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "chatterjee_xi",
    "description": "Chatterjee's xi (conventions: Chatterjee's xi; ADR 0376).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chatterjee_xi.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chatterjee_xi.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
