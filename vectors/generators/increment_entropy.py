"""Writes vectors/cases/increment_entropy.json, stdlib only.

Increment entropy (conventions: Increment entropy; ADR 0344): the increments and their
population variance exact in rationals; each size the largest k <= R with
k^2 sigma^2 <= v^2 R^2, exact, asserting each nonzero |v| R / sigma below R is at least 1e-9
from an integer; exact word counts, then -sum p ln p in float.

Run from the repo root: python vectors/generators/increment_entropy.py [--check]
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


def letters_of(x, r):
    q = [Fr(a) for a in x]
    v = [b - a for a, b in zip(q, q[1:])]
    mean = sum(v, Fr(0)) / len(v)
    var = sum(((u - mean) ** 2 for u in v), Fr(0)) / len(v)
    out = []
    for u in v:
        k = 0
        while k < r and (k + 1) ** 2 * var <= u * u * r * r:
            k += 1
        if k < r and u != 0:
            t = abs(float(u)) * r / math.sqrt(float(var))
            assert (k + 1) ** 2 * var != u * u * r * r and abs(t - round(t)) > 1e-9, (u, t)
        sign = (u > 0) - (u < 0)
        out.append((sign, k))
    return out


def add(cid, x, m, r, why):
    letters = letters_of(x, r)
    words = len(x) - m
    counts = Counter(tuple(letters[i:i + m]) for i in range(words))
    v = -math.fsum(c / words * math.log(c / words) for c in counts.values())
    cases.append({"id": f"increment_entropy.{cid}", "op": "increment_entropy",
                  "args": {"samples": x, "m": m, "levels": r}, "expected": v, "tol": TOL,
                  "source": why})
    return letters, v


letters, v = add("zigzag", [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0], 2, 3, "+-1 steps: sigma = 1, "
                 "every size min(3, 3) = 3; two words alternate, 3 and 2 times")
assert set(letters) == {(1, 3), (-1, 3)}
assert abs(v - -(0.6 * math.log(0.6) + 0.4 * math.log(0.4))) < 1e-15, v
letters, v = add("one_letter", [0.0, 1.0, 2.5, 3.5], 1, 1, "steps 1, 1.5, 1: m = 1, R = 1")
add("with_flat_steps", [0.0, 0.0, 1.0, 1.0, -0.5, -0.5, 0.25, 2.0, 2.0, 1.0], 2, 4,
    "steps with zeros: sign 0 has size 0")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.1,
              1.5, -0.75, 2.0, 0.5, -1.0], 3, 4, "eighteen arbitrary samples, m = 3, R = 4")
rng = random.Random(344)
add("noise", [rng.randint(-50, 50) / 16 for _ in range(200)], 2, 6,
    "200 random sixteenths from random.Random(344), m = 2, R = 6")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 2, "levels": 3}
    base.update(args)
    cases.append({"id": f"increment_entropy.{cid}", "op": "increment_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("levels_zero", "levels must be at least 1", levels=0)
err("levels_1001", "levels must be at most 1000", levels=1001)
err("too_short", "samples must be at least m + 1 long", m=5)
err("ramp", "every increment is 0.5, so sigma = 0", samples=[0.0, 0.5, 1.0, 1.5, 2.0])
err("inf", "samples must be finite", samples=[0.0, "inf", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "increment_entropy",
    "description": "Increment entropy (conventions: Increment entropy; ADR 0344).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "increment_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/increment_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
