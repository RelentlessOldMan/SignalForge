"""Writes vectors/cases/slope_entropy.json, stdlib only.

Slope entropy (conventions: Slope entropy; ADR 0347): the steps of dyadic samples exact in
rationals, classified against the exact thresholds into +2, +1, 0, -1, -2; exact pattern
counts; then -sum p ln p in float.

Run from the repo root: python vectors/generators/slope_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from collections import Counter
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def symbol(d, g, d0):
    if d > g:
        return 2
    if d > d0:
        return 1
    if d < -g:
        return -2
    if d < -d0:
        return -1
    return 0


def add(cid, x, m, gamma, delta, why):
    q = [Fr(v) for v in x]
    g, d0 = Fr(gamma), Fr(delta)
    s = [symbol(b - a, g, d0) for a, b in zip(q, q[1:])]
    windows = len(q) - m + 1
    counts = Counter(tuple(s[i:i + m - 1]) for i in range(windows))
    v = -math.fsum(c / windows * math.log(c / windows) for c in counts.values())
    args = {"samples": x, "m": m}
    if gamma != 1.0:
        args["gamma"] = gamma
    if delta != 1e-3:
        args["delta"] = delta
    cases.append({"id": f"slope_entropy.{cid}", "op": "slope_entropy", "args": args,
                  "expected": v, "tol": TOL, "source": why})
    return s, v


s, v = add("ramp", [0.5 * i for i in range(10)], 3, 1.0, 1e-3, "steps of 0.5: every symbol "
           "+1, so 0")
assert set(s) == {1} and v == 0.0
s, v = add("on_the_thresholds", [0.0, 1.0, 1.25, 1.25, 1.0, 0.0, 2.0, -0.5], 2, 1.0, 0.25,
           "steps 1 (= gamma: +1), 0.25 (= delta: 0), 0, -0.25 (0), -1 (-1), 2 (+2), -2.5 (-2)")
assert s == [1, 0, 0, 0, -1, 2, -2], s
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0], 3, 1.0, 0.125, "eighteen arbitrary dyadic samples")
rng = random.Random(347)
add("noise", [rng.randint(-24, 24) / 8 for _ in range(200)], 4, 1.5, 0.25,
    "200 random eighths from random.Random(347), m = 4, gamma 1.5, delta 0.25")
add("defaults", [0.0, 0.0, 2.0, 1.5, 1.5, -1.0, 0.0], 2, 1.0, 1e-3, "the default thresholds")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 2}
    base.update(args)
    cases.append({"id": f"slope_entropy.{cid}", "op": "slope_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_one", "m must be at least 2", m=1)
err("m_17", "m must be at most 16", m=17)
err("delta_negative", "delta must be at least 0", delta=-0.5)
err("delta_equal_gamma", "delta must be below gamma", gamma=0.5, delta=0.5)
err("too_short", "samples must be at least m long", m=6)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "slope_entropy",
    "description": "Slope entropy (conventions: Slope entropy; ADR 0347).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "slope_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/slope_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
