"""Writes vectors/cases/petraitis_overlap.json, stdlib only.

Petraitis' specific overlap (conventions: Petraitis' specific overlap; ADR 0599): the
shares of each record with fractions, E = sum p ln(q/p) with 60-digit decimal logarithms,
and exp(E); 0 when x uses a kind y does not. Each hand case is also checked against its
closed form.

Run from the repo root: python vectors/generators/petraitis_overlap.py [--check]
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
    e = D(0)
    v = None
    for a, b in zip(xs, ys):
        if a > 0:
            p = a / sx
            q = b / sy
            if q == 0:
                v = D(0)
                break
            e += (
                D(p.numerator)
                / D(p.denominator)
                * (D(q.numerator * p.denominator) / D(q.denominator * p.numerator)).ln()
            )
    if v is None:
        v = e.exp()
    cases.append(
        {
            "id": f"petraitis_overlap.{cid}",
            "op": "petraitis_overlap",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("proportional", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same shares: 1"), 1)
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "x uses a kind y does not: 0") == 0
assert add("unused", [1.0, 1.0], [1.0, 0.0], "x uses a kind y does not: 0") == 0
assert near(
    add("half", [1.0, 0.0], [1.0, 1.0], "shares 1, 0 on 1/2, 1/2: exp(ln 1/2) = 1/2"), D(1) / 2
)
assert near(
    add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "shares 1, 0, 0 on thirds: 1/3"), D(1) / 3
)
assert near(
    add(
        "mirror",
        [2.0, 1.0, 1.0],
        [1.0, 1.0, 2.0],
        "shares 1/2, 1/4, 1/4 on 1/4, 1/4, 1/2: E = -(1/4) ln 2, 2^(-1/4)",
    ),
    D(2) ** D("-0.25"),
)
assert near(
    add(
        "uneven",
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 5.0],
        "quarters on 1/8, 1/8, 1/8, 5/8: E = (1/4) ln(5/16), (5/16)^(1/4)",
    ),
    (D(5) / 16) ** D("0.25"),
)
assert near(
    add(
        "huge",
        [1e308, 1e308],
        [1.0, 3.0],
        "the sum of x would overflow: halves on 1/4, 3/4: (3/4)^(1/2)",
    ),
    (D(3) / 4).sqrt(),
)
assert near(
    add(
        "tiny",
        [5e-324, 0.0, 1.0],
        [1e-300, 1e-300, 1.0],
        "the smallest double counts: E about -2e-300, 1 to double precision",
    ),
    1,
)
rng = random.Random(599)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    y,
    "x then y, 25 values each from random.Random(599).choice([0, 0, 1, 2.5]) "
    "and .choice([0.5, 1, 2.5])",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"petraitis_overlap.{cid}",
            "op": "petraitis_overlap",
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
    "suite": "petraitis_overlap",
    "description": "Petraitis' specific overlap (conventions: Petraitis' specific overlap; ADR 0599).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "petraitis_overlap.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/petraitis_overlap.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
