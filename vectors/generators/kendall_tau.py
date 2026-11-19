"""Writes vectors/cases/kendall_tau.json, stdlib only.

Kendall's tau-b (conventions: Kendall's tau-b; ADR 0370): the pair and tie counts in
integers, then the square root and the quotient in float.

Run from the repo root: python vectors/generators/kendall_tau.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from collections import Counter

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def sign(v):
    return (v > 0) - (v < 0)


def add(cid, x, y, why):
    n = len(x)
    s = sum(sign(x[j] - x[i]) * sign(y[j] - y[i]) for i in range(n) for j in range(i + 1, n))
    n0 = n * (n - 1) // 2
    n1 = sum(t * (t - 1) // 2 for t in Counter(x).values())
    n2 = sum(t * (t - 1) // 2 for t in Counter(y).values())
    tau = s / math.sqrt(float((n0 - n1) * (n0 - n2)))
    cases.append({"id": f"kendall_tau.{cid}", "op": "kendall_tau", "args": {"x": x, "y": y},
                  "expected": tau, "tol": TOL, "source": why})
    return s, n0, n1, n2, tau


s, n0, n1, n2, tau = add("one_swap", [1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0],
                         "6 pairs, one discordant (2,3): (5 - 1)/6 = 2/3")
assert s == 4 and n0 == 6 and n1 == n2 == 0
s, n0, n1, n2, tau = add("reversed", [0.5, 1.5, 2.5], [9.0, 4.0, -1.0], "all discordant: -1")
assert tau == -1.0
s, n0, n1, n2, tau = add("ties", [1.0, 2.0, 2.0, 3.0], [1.0, 1.0, 2.0, 3.0],
                         "pairs: (0,1) +0, (0,2) +1, (0,3) +1, (1,2) 0, (1,3) +1, (2,3) +1: "
                         "4; one tie in each: 4/sqrt(5*5) = 4/5")
assert s == 4 and n1 == n2 == 1
rng = random.Random(370)
xs = [rng.randint(-20, 20) / 4 for _ in range(70)]
ys = [v + rng.randint(-20, 20) / 4 for v in xs]
add("noisy_pair", xs, ys,
    "70 random quarters from random.Random(370) and the same plus more, with ties")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5], "y": [2.0, 1.0, 3.0]}
    base.update(args)
    cases.append({"id": f"kendall_tau.{cid}", "op": "kendall_tau", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0])
err("one_sample", "N must be at least 2", x=[1.0], y=[2.0])
err("constant_x", "x must not be constant", x=[1.0, 1.0, 1.0])
err("constant_y", "y must not be constant", y=[1.0, 1.0, 1.0])
err("nan", "samples must be finite", x=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "kendall_tau",
    "description": "Kendall's tau-b (conventions: Kendall's tau-b; ADR 0370).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kendall_tau.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kendall_tau.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
