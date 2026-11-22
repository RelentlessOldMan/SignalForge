"""Writes vectors/cases/morisita_overlap.json, stdlib only.

Morisita's overlap of two count records (conventions: Morisita's overlap of two count
records; ADR 0581): the totals, sum(x y) and sum(n(n - 1)) with fractions.

Run from the repo root: python vectors/generators/morisita_overlap.py [--check]
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
    xs = [int(a) for a in x]
    ys = [int(b) for b in y]
    bx, by = sum(xs), sum(ys)
    cross = sum(a * b for a, b in zip(xs, ys))
    sx = sum(a * (a - 1) for a in xs)
    sy = sum(b * (b - 1) for b in ys)
    lam = Fr(sx, bx * (bx - 1)) + Fr(sy, by * (by - 1))
    f = Fr(2 * cross) / (lam * bx * by)
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"morisita_overlap.{cid}",
            "op": "morisita_overlap",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("disjoint", [2.0, 0.0], [0.0, 2.0], "no shared kind: 0") == 0
assert add("crossed", [3.0, 1.0], [1.0, 3.0], "l = 1/2 each, 2*6/(1*16) = 3/4") == D(3) / 4
assert add("identical", [5.0, 5.0], [5.0, 5.0], "l = 4/9 each, 2*50/((8/9)*100) = 9/8") == D(9) / 8
assert (
    add(
        "one_side", [4.0, 0.0, 2.0], [1.0, 1.0, 1.0], "l_x = 14/30, l_y = 0: 2*6/((7/15)*18) = 10/7"
    )
    == D(10) / 7
)
assert add("singletons", [1.0, 1.0], [2.0, 0.0], "l_x = 0, l_y = 1: 2*2/(1*4) = 1") == 1
assert (
    add(
        "large",
        [10_000_000.0, 0.0],
        [10_000_000.0, 0.0],
        "one kind each at the total limit: l = 1, 2*10^14/(2*10^14) = 1",
    )
    == 1
)
assert (
    add(
        "three",
        [6.0, 3.0, 1.0],
        [2.0, 2.0, 6.0],
        "X = Y = 10, l_x = 36/90, l_y = 34/90: 2*24/((70/90)*100) = 108/175",
    )
    == D(108) / 175
)
rng = random.Random(581)
x = [float(rng.choice([0, 0, 1, 2, 5])) for _ in range(25)]
y = [float(rng.choice([0, 0, 1, 2, 5])) for _ in range(25)]
add("random", x, y, "x then y, 25 counts each from random.Random(581).choice([0, 0, 1, 2, 5])")


def err(cid, why, **args):
    base = {"x": [2.0, 1.0, 0.0], "y": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"morisita_overlap.{cid}",
            "op": "morisita_overlap",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], y=[])
err("negative", "counts must be at least 0", y=[1.0, -1.0, 2.0])
err("fraction", "counts must be whole", y=[1.5, 1.0, 1.0])
err("total_one", "each record must total at least 2", x=[1.0, 0.0, 0.0])
err("too_large", "each record must total at most 10 000 000", x=[10_000_001.0, 0.0, 0.0])
err("all_ones", "some count must be above 1", x=[1.0, 1.0, 0.0], y=[0.0, 1.0, 1.0])
err("lengths", "the records must have the same length", y=[1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "morisita_overlap",
    "description": "Morisita's overlap of two count records (conventions: Morisita's overlap of two count records; ADR 0581).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "morisita_overlap.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/morisita_overlap.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
