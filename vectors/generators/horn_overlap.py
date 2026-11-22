"""Writes vectors/cases/horn_overlap.json, stdlib only.

Horn's information overlap (conventions: Horn's information overlap; ADR 0574): the
definition evaluated directly from the exact values in 60-digit decimal.

Run from the repo root: python vectors/generators/horn_overlap.py [--check]
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


def xlnx(f):
    if f == 0:
        return D(0)
    d = D(f.numerator) / D(f.denominator)
    return d * d.ln()


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    tx = sum(xs, Fr(0))
    ty = sum(ys, Fr(0))
    num = sum((xlnx(a + b) - xlnx(a) - xlnx(b) for a, b in zip(xs, ys)), D(0))
    v = num / (xlnx(tx + ty) - xlnx(tx) - xlnx(ty))
    cases.append(
        {
            "id": f"horn_overlap.{cid}",
            "op": "horn_overlap",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("same", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "identical records: 1"), 1)
assert near(add("proportional", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "proportional records: 1"), 1)
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "no shared kind: 0") == 0
ln2, ln3, ln7 = D(2).ln(), D(3).ln(), D(7).ln()
assert near(
    add("half", [1.0, 1.0], [1.0, 0.0], "2 ln 2/(3 ln 3 - 2 ln 2)"), 2 * ln2 / (3 * ln3 - 2 * ln2)
)
assert near(add("swapped", [1.0, 3.0], [3.0, 1.0], "2 - (3/4) log2 3"), 2 - D(3) / 4 * ln3 / ln2)
assert near(
    add(
        "huge",
        [1e300, 2e300],
        [3e300, 1e300],
        "6 ln 2/(7 ln 7 - 3 ln 3 - 8 ln 2): totals would overflow",
    ),
    6 * ln2 / (7 * ln7 - 3 * ln3 - 8 * ln2),
)
add("unequal_totals", [1.0, 2.0, 3.0], [30.0, 20.0, 10.0], "totals 6 and 60")
add("tiny", [1e-300, 3e-301, 0.0], [2e-300, 5e-300, 1e-300], "values near the bottom of the range")
rng = random.Random(574)
x = [round(rng.uniform(0, 5), 3) for _ in range(25)]
y = [round(rng.uniform(0, 5), 3) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(574).uniform(0, 5), 3 places")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"horn_overlap.{cid}",
            "op": "horn_overlap",
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
    "suite": "horn_overlap",
    "description": "Horn's information overlap (conventions: Horn's information overlap; ADR 0574).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "horn_overlap.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/horn_overlap.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
