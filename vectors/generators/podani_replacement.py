"""Writes vectors/cases/podani_replacement.json, stdlib only.

Podani's replacement part of the Jaccard dissimilarity (conventions: Podani's replacement
part of the Jaccard dissimilarity; ADR 0584): presence counts and 2 min(b, c)/(a + b + c) with
fractions.

Run from the repo root: python vectors/generators/podani_replacement.py [--check]
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
TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    both = sum(1 for a, b in zip(xs, ys) if a > 0 and b > 0)
    only_x = sum(1 for a, b in zip(xs, ys) if a > 0 and b == 0)
    only_y = sum(1 for a, b in zip(xs, ys) if a == 0 and b > 0)
    least = min(only_x, only_y)
    f = Fr(2 * least, both + only_x + only_y)
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"podani_replacement.{cid}",
            "op": "podani_replacement",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("same", [1.0, 2.0, 3.0], [5.0, 0.5, 1.0], "the same kinds: 0") == 0
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "no shared kind, b = c = 1: 2/2 = 1") == 1
assert add("subset", [1.0, 1.0], [1.0, 0.0], "y's kinds are in x: 0") == 0
assert (
    add("crossed", [1.0, 2.0, 0.0, 4.0], [0.0, 3.0, 5.0, 1.0], "a = 2, b = c = 1: 2/4") == D(1) / 2
)
assert add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "x's kinds are in y: 0") == 0
assert (
    add("swap", [1.0, 1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 1.0, 1.0], "a = 1, b = c = 2: 4/5")
    == D(4) / 5
)
assert (
    add(
        "uneven",
        [1.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "a = 1, b = 4, c = 1: 2/6",
    )
    == D(1) / 3
)
assert (
    add(
        "tiny",
        [5e-324, 0.0, 1.0],
        [0.0, 1e-300, 1.0],
        "the smallest double counts as present: a = b = c = 1: 2/3",
    )
    == D(2) / 3
)
rng = random.Random(584)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(584).choice([0, 0, 1, 2.5])")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"podani_replacement.{cid}",
            "op": "podani_replacement",
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
    "suite": "podani_replacement",
    "description": "Podani's replacement part of the Jaccard dissimilarity (conventions: Podani's replacement part of the Jaccard dissimilarity; ADR 0584).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "podani_replacement.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/podani_replacement.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
