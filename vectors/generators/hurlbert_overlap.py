"""Writes vectors/cases/hurlbert_overlap.json, stdlib only.

Hurlbert's niche overlap (conventions: Hurlbert's niche overlap; ADR 0600): the shares
of each record and sum p q / r with fractions.

Run from the repo root: python vectors/generators/hurlbert_overlap.py [--check]
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


def add(cid, x, y, available, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    avs = [Fr(c) for c in available]
    sx = sum(xs)
    sy = sum(ys)
    sa = sum(avs)
    f = sum(a / sx * (b / sy) / (c / sa) for a, b, c in zip(xs, ys, avs))
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"hurlbert_overlap.{cid}",
            "op": "hurlbert_overlap",
            "args": {"x": x, "y": y, "available": available},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert (
    add(
        "as_available",
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
        "both use the kinds as they are available: sum r = 1",
    )
    == 1
)
assert (
    add(
        "crowded",
        [1.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        "halves on quarters: 2 (1/4)/(1/4) = 2",
    )
    == 2
)
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], [1.0, 1.0], "no kind in common: 0") == 0
assert add("one_sided", [1.0, 0.0], [1.0, 1.0], [1.0, 1.0], "1 (1/2)/(1/2) = 1") == 1
assert (
    add(
        "uneven",
        [2.0, 1.0, 1.0],
        [1.0, 1.0, 2.0],
        [1.0, 2.0, 1.0],
        "(1/8)/(1/4) + (1/16)/(1/2) + (1/8)/(1/4) = 9/8",
    )
    == D(9) / 8
)
assert (
    add("scarce", [1.0, 1.0], [1.0, 1.0], [1.0, 3.0], "(1/4)/(1/4) + (1/4)/(3/4) = 4/3") == D(4) / 3
)
assert (
    add(
        "huge",
        [1e308, 1e308],
        [1.0, 3.0],
        [1e308, 1e308],
        "the sums of x and available would overflow: (1/8)/(1/2) + (3/8)/(1/2) = 1",
    )
    == 1
)
assert near(
    add(
        "tiny",
        [5e-324, 0.0, 1.0],
        [1e-300, 1e-300, 1.0],
        [1.0, 1.0, 1.0],
        "the smallest double counts: 3 (1 + 5e-624)/((1 + 5e-324)(1 + 2e-300)), "
        "3 to double precision",
    ),
    3,
)
rng = random.Random(600)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
available = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    y,
    available,
    "x, y then available, 25 values each from random.Random(600)"
    ".choice([0, 0, 1, 2.5]), twice, and .choice([0.5, 1, 2.5])",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0], "available": [1.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hurlbert_overlap.{cid}",
            "op": "hurlbert_overlap",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], y=[], available=[])
err("negative", "values must be at least 0", y=[1.0, -0.5, 2.0])
err("all_zero", "each record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", y=[1.0, 2.0])
err("unavailable", "available must be above 0 everywhere", available=[1.0, 0.0, 1.0])
err("underflow", "the share 5e-324/1e300 underflows to 0", available=[1e300, 5e-324, 1.0])
err(
    "overflow",
    "(1/3)(1/3)/(1e-310/(2 + 1e-310)) is above the largest double",
    x=[1.0, 1.0, 1.0],
    y=[1.0, 1.0, 1.0],
    available=[1.0, 1e-310, 1.0],
)

doc = {
    "schema": 1,
    "suite": "hurlbert_overlap",
    "description": "Hurlbert's niche overlap (conventions: Hurlbert's niche overlap; ADR 0600).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hurlbert_overlap.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hurlbert_overlap.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
