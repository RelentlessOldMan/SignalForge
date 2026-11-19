"""Writes vectors/cases/turning_points.json, stdlib only.

Turning point test (conventions: Turning point test; ADR 0360): the count by exact
comparisons; count - 2(N-2)/3 and (16N-29)/90 in rationals; then the square root and the
quotient in float.

Run from the repo root: python vectors/generators/turning_points.py [--check]
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


def add(cid, x, why):
    n = len(x)
    k = sum(1 for i in range(1, n - 1)
            if (x[i - 1] < x[i] > x[i + 1]) or (x[i - 1] > x[i] < x[i + 1]))
    z = float(k - Fr(2 * (n - 2), 3)) / math.sqrt(float(Fr(16 * n - 29, 90)))
    cases.append({"id": f"turning_points.{cid}", "op": "turning_points",
                  "args": {"samples": x}, "expected": {"count": k, "z": z}, "tol": TOL,
                  "source": why})
    return k, z


k, z = add("three_by_hand", [0.0, 1.0, 0.0],
           "one peak: count 1, mean 2/3, variance 19/90: z = (1/3)/sqrt(19/90)")
assert k == 1 and abs(z - (1 / 3) / math.sqrt(19 / 90)) < 1e-15
k, z = add("ramp", [float(t) for t in range(10)],
           "a ramp has no turning points: z = -(16/3)/sqrt(131/90)")
assert k == 0
k, z = add("alternating", [1.0, -1.0] * 6, "twelve alternating samples: all ten inner turn")
assert k == 10
k, z = add("ties", [0.0, 1.0, 1.0, 0.0, 2.0, 2.0, 2.0, 3.0],
           "plateaus are not turning points; only the dip at index 3 counts")
assert k == 1
rng = random.Random(360)
add("noise", [rng.random() for _ in range(500)],
    "500 uniform floats from random.Random(360)")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"turning_points.{cid}", "op": "turning_points", "args": base,
                  "error": "invalid_argument", "source": why})


err("too_short", "N must be at least 3", samples=[0.0, 1.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "turning_points",
    "description": "Turning point test (conventions: Turning point test; ADR 0360).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "turning_points.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/turning_points.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
