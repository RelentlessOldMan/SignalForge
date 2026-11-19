"""Writes vectors/cases/spearman_correlation.json, stdlib only.

Spearman rank correlation (conventions: Spearman rank correlation; ADR 0369): mean ranks and
the three sums exact in rationals, then the square root and the quotient in float.

Run from the repo root: python vectors/generators/spearman_correlation.py [--check]
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


def ranks(x):
    # Each value's rank is the number below it plus half of (the number equal to it, plus 1).
    return [sum(1 for u in x if u < v) + Fr(sum(1 for u in x if u == v) + 1, 2) for v in x]


def add(cid, x, y, why):
    n = len(x)
    c = Fr(n + 1, 2)
    r = [v - c for v in ranks(x)]
    s = [v - c for v in ranks(y)]
    rs = sum((u * w for u, w in zip(r, s)), Fr(0))
    rr = sum((u * u for u in r), Fr(0))
    ss = sum((w * w for w in s), Fr(0))
    rho = float(rs) / math.sqrt(float(rr * ss))
    cases.append({"id": f"spearman_correlation.{cid}", "op": "spearman_correlation",
                  "args": {"x": x, "y": y}, "expected": rho, "tol": TOL, "source": why})
    return rs, rr, ss, rho


rs, rr, ss, rho = add("monotone_not_linear", [1.0, 2.0, 3.0, 4.0, 5.0],
                      [1.0, 8.0, 27.0, 64.0, 125.0], "y = x^3: the ranks agree, rho = 1")
assert rs == rr == ss and rho == 1.0
rs, rr, ss, rho = add("reversed", [0.5, 1.5, 2.5], [9.0, 4.0, -1.0], "ranks reversed: -1")
assert rho == -1.0
rs, rr, ss, rho = add("by_hand", [1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0],
                      "ranks 1,2,3,4 and 1,3,2,4: centred -3/2,-1/2,1/2,3/2 and "
                      "-3/2,1/2,-1/2,3/2; sum of products 9/4-1/4-1/4+9/4 = 4, each sum of "
                      "squares 5: rho = 4/5")
assert rs == 4 and rr == ss == 5
rs, rr, ss, rho = add("ties", [1.0, 2.0, 2.0, 3.0], [1.0, 1.0, 2.0, 3.0],
                      "ranks 1, 5/2, 5/2, 4 and 3/2, 3/2, 3, 4: centred -3/2,0,0,3/2 and "
                      "-1,-1,1/2,3/2; products 3/2 + 9/4 = 15/4; squares 9/2 and 9/2: "
                      "rho = 15/4 / (9/2) = 5/6")
assert rs == Fr(15, 4) and rr == ss == Fr(9, 2)
rng = random.Random(369)
xs = [rng.randint(-40, 40) / 8 for _ in range(60)]
ys = [v + rng.randint(-40, 40) / 8 for v in xs]
add("noisy_pair", xs, ys,
    "60 random eighths from random.Random(369) and the same plus more random eighths, "
    "with ties")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5], "y": [2.0, 1.0, 3.0]}
    base.update(args)
    cases.append({"id": f"spearman_correlation.{cid}", "op": "spearman_correlation",
                  "args": base, "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0])
err("one_sample", "N must be at least 2", x=[1.0], y=[2.0])
err("constant_x", "x must not be constant", x=[1.0, 1.0, 1.0])
err("constant_y", "y must not be constant", y=[1.0, 1.0, 1.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "spearman_correlation",
    "description": "Spearman rank correlation (conventions: Spearman rank correlation; "
                   "ADR 0369).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spearman_correlation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spearman_correlation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
