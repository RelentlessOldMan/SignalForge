"""Writes vectors/cases/bartels_rank_test.json, stdlib only.

Bartels rank test (conventions: Bartels rank test; ADR 0363): mean ranks for ties, the ratio
and the variance exact in rationals, then the square root and the quotient in float.

Run from the repo root: python vectors/generators/bartels_rank_test.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def ranks(x):
    out = []
    for v in x:
        below = sum(1 for u in x if u < v)
        equal = sum(1 for u in x if u == v)
        out.append(below + Fr(equal + 1, 2))
    return out


def add(cid, x, why):
    n = len(x)
    r = ranks(x)
    centre = Fr(n + 1, 2)
    ratio = (sum(((b - a) ** 2 for a, b in zip(r, r[1:])), Fr(0))
             / sum(((u - centre) ** 2 for u in r), Fr(0)))
    var = Fr(4 * (n - 2) * (5 * n * n - 2 * n - 9), 5 * n * (n + 1) * (n - 1) ** 2)
    z = float(ratio - 2) / math.sqrt(float(var))
    cases.append({"id": f"bartels_rank_test.{cid}", "op": "bartels_rank_test",
                  "args": {"samples": x}, "expected": {"ratio": float(ratio), "z": z},
                  "tol": TOL, "source": why})
    return r, ratio, var


r, ratio, var = add("three_by_hand", [5.0, -2.0, 7.0],
                    "ranks 2, 1, 3: differences 1 and 2 give 5 over deviations 0 + 1 + 1: "
                    "ratio 5/2; variance 4*1*30/(5*3*4*4) = 1/2")
assert r == [2, 1, 3] and ratio == Fr(5, 2) and var == Fr(1, 2)
r, ratio, var = add("ties_by_hand", [1.0, 1.0, 3.0, 0.0],
                    "ranks 2.5, 2.5, 4, 1: numerator 0 + 2.25 + 9 = 45/4, deviations "
                    "0 + 0 + 9/4 + 9/4 = 9/2: ratio 5/2")
assert r == [Fr(5, 2), Fr(5, 2), 4, 1] and ratio == Fr(5, 2)
r, ratio, var = add("trend", [float(t) for t in range(20)],
                    "a ramp: ranks 1 to 20, 19 over 20*399/12 = 665: ratio 1/35")
assert ratio == Fr(1, 35)
rng = random.Random(363)
add("noise", [rng.randint(-50, 50) / 8 for _ in range(300)],
    "300 random eighths from random.Random(363), with many ties")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"bartels_rank_test.{cid}", "op": "bartels_rank_test", "args": base,
                  "error": "invalid_argument", "source": why})


err("too_short", "N must be at least 3", samples=[0.0, 1.0])
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "bartels_rank_test",
    "description": "Bartels rank test (conventions: Bartels rank test; ADR 0363).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bartels_rank_test.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bartels_rank_test.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
