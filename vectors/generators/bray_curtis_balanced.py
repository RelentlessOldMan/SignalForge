"""Writes vectors/cases/bray_curtis_balanced.json, stdlib only.

The balanced-variation part of the Bray-Curtis dissimilarity (conventions: balanced-variation
part of the Bray-Curtis dissimilarity; ADR 0582): A, B, C and min(B, C)/(A + min(B, C)) with
fractions.

Run from the repo root: python vectors/generators/bray_curtis_balanced.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 60
TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    shared = sum(min(a, b) for a, b in zip(xs, ys))
    least = min(sum(xs) - shared, sum(ys) - shared)
    f = least / (shared + least)
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"bray_curtis_balanced.{cid}",
            "op": "bray_curtis_balanced",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("same", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "identical records: B = C = 0") == 0
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "nothing shared: 1/(0 + 1) = 1") == 1
assert add("double", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "y is at least x everywhere: 0") == 0
assert (
    add("crossed", [1.0, 2.0, 0.0, 4.0], [0.0, 3.0, 5.0, 1.0], "A = 3, B = 4, C = 6: 4/7")
    == D(4) / 7
)
assert add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "A = 1, B = 0, C = 2: 0") == 0
assert (
    add(
        "huge",
        [1.5e308, 1.5e308, 0.0],
        [1.5e308, 0.0, 1.5e308],
        "sums past the largest double, A = B = C: 1/2",
    )
    == D(1) / 2
)
assert (
    add("tiny", [1e-323, 5e-324], [5e-324, 1e-323], "subnormal values, A = 2B = 2C: 1/3")
    == D(1) / 3
)
assert (
    add(
        "uneven",
        [1.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "presence records, A = 1, B = 4, C = 1: 1/2",
    )
    == D(1) / 2
)
rng = random.Random(582)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(582).choice([0, 0, 1, 2.5])")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"bray_curtis_balanced.{cid}",
            "op": "bray_curtis_balanced",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], y=[])
err("negative", "values must be at least 0", y=[1.0, -0.5, 2.0])
err("all_zero", "each record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", y=[1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "bray_curtis_balanced",
    "description": "The balanced-variation part of the Bray-Curtis dissimilarity (conventions: balanced-variation part of the Bray-Curtis dissimilarity; ADR 0582).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bray_curtis_balanced.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bray_curtis_balanced.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
