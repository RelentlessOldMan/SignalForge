"""Writes vectors/cases/mann_kendall.json, stdlib only.

Mann-Kendall trend test (conventions: Mann-Kendall trend test; ADR 0364): S and the
tie-corrected variance exact as integers, then the square root and the quotient in float.

Run from the repo root: python vectors/generators/mann_kendall.py [--check]
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


def add(cid, x, why):
    n = len(x)
    s = sum((x[j] > x[i]) - (x[j] < x[i]) for i in range(n) for j in range(i + 1, n))
    var = Fr(n * (n - 1) * (2 * n + 5)
             - sum(t * (t - 1) * (2 * t + 5) for t in Counter(x).values()), 18)
    z = 0.0 if s == 0 else (s - 1 if s > 0 else s + 1) / math.sqrt(float(var))
    cases.append({"id": f"mann_kendall.{cid}", "op": "mann_kendall", "args": {"samples": x},
                  "expected": {"s": s, "z": z}, "tol": TOL, "source": why})
    return s, var, z


s, var, z = add("rising_by_hand", [1.0, 2.0, 3.0, 4.0],
                "all six pairs rise: S = 6; variance 4*3*13/18 = 26/3; z = 5/sqrt(26/3)")
assert (s, var) == (6, Fr(26, 3))
s, var, z = add("ties_by_hand", [1.0, 1.0, 2.0, 0.0],
                "pairs: 0, +1, -1, +1, -1, -1: S = -1; one tie of 2 removes 2*1*9 = 18: "
                "variance (156 - 18)/18 = 23/3; z = 0")
assert (s, var, z) == (-1, Fr(23, 3), 0.0)
s, var, z = add("falling", [5.0, 3.0, 4.0, 1.0, 0.0],
                "nine of ten pairs fall, one rises: S = -8; variance 5*4*15/18 = 50/3")
assert (s, var) == (-8, Fr(50, 3))
s, var, z = add("symmetric", [0.0, 1.0, 0.0], "one rise, one fall, one tie: S = 0, z = 0")
assert (s, z) == (0, 0.0)
rng = random.Random(364)
add("trend_in_noise", [t / 64 + rng.randint(-20, 20) / 8 for t in range(200)],
    "a slow ramp plus random eighths from random.Random(364)")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"mann_kendall.{cid}", "op": "mann_kendall", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_sample", "N must be at least 2", samples=[1.0])
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "mann_kendall",
    "description": "Mann-Kendall trend test (conventions: Mann-Kendall trend test; ADR 0364).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mann_kendall.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mann_kendall.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
