"""Writes vectors/cases/schoener_overlap.json, stdlib only.

Schoener's overlap (conventions: Schoener's overlap; ADR 0598): the shares of each
record and 1 - (1/2) sum |p - q| with fractions.

Run from the repo root: python vectors/generators/schoener_overlap.py [--check]
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
    sx = sum(xs)
    sy = sum(ys)
    f = 1 - Fr(1, 2) * sum(abs(a / sx - b / sy) for a, b in zip(xs, ys))
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"schoener_overlap.{cid}",
            "op": "schoener_overlap",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("proportional", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same shares: 1") == 1
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "no kind in common: 0") == 0
assert (
    add(
        "mixed",
        [1.0, 2.0, 3.0],
        [5.0, 0.5, 1.0],
        "shares 1/6, 1/3, 1/2 and 10/13, 1/13, 2/13: 1/6 + 1/13 + 2/13 = 31/78",
    )
    == D(31) / 78
)
assert add("half", [1.0, 1.0], [1.0, 0.0], "shares 1/2, 1/2 and 1, 0: 1/2") == D(1) / 2
assert (
    add("mirror", [2.0, 1.0, 1.0], [1.0, 1.0, 2.0], "shares 1/2, 1/4, 1/4 and 1/4, 1/4, 1/2: 3/4")
    == D(3) / 4
)
assert add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "shares 1, 0, 0 and thirds: 1/3") == D(1) / 3
assert (
    add(
        "huge",
        [1e308, 1e308],
        [1.0, 3.0],
        "the sum of x would overflow: shares 1/2, 1/2 and 1/4, 3/4: 3/4",
    )
    == D(3) / 4
)
assert near(
    add(
        "tiny",
        [5e-324, 0.0, 1.0],
        [0.0, 1e-300, 1.0],
        "the smallest double counts: 1/(1 + 1e-300), 1 to double precision",
    ),
    1,
)
rng = random.Random(598)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(598).choice([0, 0, 1, 2.5])")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"schoener_overlap.{cid}",
            "op": "schoener_overlap",
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
    "suite": "schoener_overlap",
    "description": "Schoener's overlap of two records (conventions: Schoener's overlap; ADR 0598).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "schoener_overlap.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/schoener_overlap.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
