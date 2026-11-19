"""Writes vectors/cases/von_neumann_ratio.json, stdlib only.

von Neumann ratio (conventions: von Neumann ratio; ADR 0362): both sums and their ratio exact
in rationals from dyadic samples.

Run from the repo root: python vectors/generators/von_neumann_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, why):
    q = [Fr(v) for v in x]
    mean = sum(q, Fr(0)) / len(q)
    den = sum(((u - mean) ** 2 for u in q), Fr(0))
    num = sum(((b - a) ** 2 for a, b in zip(q, q[1:])), Fr(0))
    v = num / den
    cases.append({"id": f"von_neumann_ratio.{cid}", "op": "von_neumann_ratio",
                  "args": {"samples": x}, "expected": float(v), "tol": TOL, "source": why})
    return v


v = add("alternating_by_hand", [1.0, -1.0, 1.0, -1.0],
        "three differences of 2: 12 over four squared deviations of 1: 3")
assert v == 3
v = add("two_samples", [0.0, 1.0], "one difference of 1 over deviations 1/4 + 1/4: 2")
assert v == 2
v = add("ramp", [float(t) for t in range(10)],
        "ten unit steps: 9 over sum (t - 4.5)^2 = 82.5, so 6/55")
assert v == Fr(6, 55)
rng = random.Random(362)
add("noise", [rng.randint(-100, 100) / 64 for _ in range(500)],
    "500 random 64ths from random.Random(362)")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"von_neumann_ratio.{cid}", "op": "von_neumann_ratio", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_sample", "N must be at least 2", samples=[1.0])
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "von_neumann_ratio",
    "description": "von Neumann ratio (conventions: von Neumann ratio; ADR 0362).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "von_neumann_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/von_neumann_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
