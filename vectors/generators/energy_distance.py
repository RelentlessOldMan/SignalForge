"""Writes vectors/cases/energy_distance.json, stdlib only.

The energy distance (conventions: energy distance; ADR 0404): the three mean absolute
differences exact in rationals.

Run from the repo root: python vectors/generators/energy_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def mean_gap(p, q):
    return Fr(sum(abs(Fr(u) - Fr(v)) for u in p for v in q), len(p) * len(q))


def add(cid, x, y, why):
    e = 2 * mean_gap(x, y) - mean_gap(x, x) - mean_gap(y, y)
    cases.append(
        {
            "id": f"energy_distance.{cid}",
            "op": "energy_distance",
            "args": {"x": x, "y": y},
            "expected": float(e),
            "tol": TOL,
            "source": why,
        }
    )
    return e


got = add("one_each", [1.0], [4.0], "one value each: 2*3 - 0 - 0 = 6")
assert got == 6
got = add("same", [3.0, 1.0, 2.0], [2.0, 3.0, 1.0], "the same values: 0")
assert got == 0
got = add("hand", [0.0, 2.0], [1.0], "A = 1, B = (0 + 2 + 2 + 0)/4 = 1, C = 0: 2 - 1 = 1")
assert got == 1
got = add(
    "hand_two",
    [0.0, 0.0],
    [0.0, 3.0],
    "A = (0 + 3 + 0 + 3)/4 = 3/2, B = 0, C = 6/4 = 3/2: 3 - 3/2 = 3/2",
)
assert got == Fr(3, 2)
rng = random.Random(404)
x = [rng.gauss(0.3, 1.0) for _ in range(40)]
y = [rng.gauss(0.0, 2.0) for _ in range(55)]
add("gaussian", x, y, "40 and 55 values from random.Random(404), N(0.3, 1) and N(0, 2)")


def integral(x, y):
    # E = 2 * integral of (F_x - F_y)^2 dt, an independent route for the check below.
    t = sorted(set(Fr(v) for v in x + y))
    area = Fr(0)
    for a, b in zip(t, t[1:]):
        fx = Fr(sum(Fr(v) <= a for v in x), len(x))
        fy = Fr(sum(Fr(v) <= a for v in y), len(y))
        area += (fx - fy) ** 2 * (b - a)
    return 2 * area


for c in cases:
    assert Fr(c["expected"]) == Fr(float(integral(c["args"]["x"], c["args"]["y"]))), c["id"]


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"energy_distance.{cid}",
            "op": "energy_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_empty", "y needs a value", y=[])
err("not_finite", "values must be finite", y=["-inf", 1.0])

doc = {
    "schema": 1,
    "suite": "energy_distance",
    "description": "The energy distance (conventions: energy distance; ADR 0404).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "energy_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/energy_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
