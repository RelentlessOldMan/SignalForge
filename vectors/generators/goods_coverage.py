"""Writes vectors/cases/goods_coverage.json, stdlib only.

Good's coverage (conventions: Good's coverage; ADR 0544): formed exactly in rationals.

Run from the repo root: python vectors/generators/goods_coverage.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    q = 1 - Fr(sum(1 for a in v if a == 1)) / total
    cases.append(
        {
            "id": f"goods_coverage.{cid}",
            "op": "goods_coverage",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("all_ones", [1.0] * 4, "F1 = N = 4: 0") == 0
assert add("no_ones", [2.0] * 4, "F1 = 0: 1") == 1
assert add("two", [3.0, 1.0], "F1 = 1, N = 4: 3/4") == Fr(3, 4)
assert add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "F1 = 2, N = 9: 7/9") == Fr(7, 9)
assert add("halves", [0.5, 0.5], "F1 = 0, N = 1: 1") == 1
assert add("single_one", [1.0], "F1 = N = 1: 0") == 0
assert add("ramp", [4.0, 1.0, 3.0, 2.0], "F1 = 1, N = 10: 9/10") == Fr(9, 10)
assert add("below_one", [0.25, 1.0, 0.25], "F1 = 1, N = 3/2: 1/3") == Fr(1, 3)
rng = random.Random(544)
x = [float(rng.randint(0, 4)) for _ in range(30)]
add("random", x, "30 whole values from random.Random(544).randint(0, 4)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"goods_coverage.{cid}",
            "op": "goods_coverage",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "goods_coverage",
    "description": "Good's coverage (conventions: Good's coverage; ADR 0544).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "goods_coverage.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/goods_coverage.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
