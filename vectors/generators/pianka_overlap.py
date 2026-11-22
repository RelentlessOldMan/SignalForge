"""Writes vectors/cases/pianka_overlap.json, stdlib only.

Pianka's niche overlap (conventions: Pianka's niche overlap; ADR 0571): the square
(sum xy)^2/(sum x^2 sum y^2) exactly with fractions, then its square root in 60-digit decimal.

Run from the repo root: python vectors/generators/pianka_overlap.py [--check]
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
TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    sxy = sum((a * b for a, b in zip(xs, ys)), Fr(0))
    sq = sxy * sxy / (sum((a * a for a in xs), Fr(0)) * sum((b * b for b in ys), Fr(0)))
    v = (D(sq.numerator) / D(sq.denominator)).sqrt()
    cases.append(
        {
            "id": f"pianka_overlap.{cid}",
            "op": "pianka_overlap",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("same", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "identical records: 1") == 1
assert add("proportional", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "proportional records: 1") == 1
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "no shared resource: 0") == 0
assert near(add("half", [1.0, 1.0], [1.0, 0.0], "1/sqrt 2"), 1 / D(2).sqrt())
assert near(add("reversed", [1.0, 2.0, 3.0], [3.0, 2.0, 1.0], "10/14 = 5/7"), D(5) / 7)
assert near(add("shifted", [1.0, 1.0, 2.0], [2.0, 1.0, 1.0], "5/6"), D(5) / 6)
assert near(
    add("huge", [1e300, 2e300], [1.0, 3.0], "7/sqrt 50: squares would overflow"), 7 / D(50).sqrt()
)
add("tiny", [1e-300, 3e-301, 0.0], [2.0, 5.0, 1.0], "values near the bottom of the range")
rng = random.Random(571)
x = [round(rng.uniform(0, 5), 3) for _ in range(25)]
y = [round(rng.uniform(0, 5), 3) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(571).uniform(0, 5), 3 places")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"pianka_overlap.{cid}",
            "op": "pianka_overlap",
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
    "suite": "pianka_overlap",
    "description": "Pianka's niche overlap (conventions: Pianka's niche overlap; ADR 0571).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pianka_overlap.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pianka_overlap.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
