"""Writes vectors/cases/cohen_d.json, stdlib only.

Cohen's d (conventions: Cohen's d; ADR 0397): the means and sums of squares exact in
rationals, the root in 40-digit decimal.

Run from the repo root: python vectors/generators/cohen_d.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
decimal.getcontext().prec = 40
cases = []


def exact(x, y):
    fx, fy = [Fr(v) for v in x], [Fr(v) for v in y]
    mx, my = sum(fx) / len(fx), sum(fy) / len(fy)
    ss = sum((v - mx) ** 2 for v in fx) + sum((v - my) ** 2 for v in fy)
    return mx - my, ss / (len(x) + len(y) - 2)


def add(cid, x, y, why):
    diff, var = exact(x, y)
    root = (decimal.Decimal(var.numerator) / decimal.Decimal(var.denominator)).sqrt()
    d = decimal.Decimal(diff.numerator) / decimal.Decimal(diff.denominator) / root
    cases.append(
        {
            "id": f"cohen_d.{cid}",
            "op": "cohen_d",
            "args": {"x": x, "y": y},
            "expected": float(d),
            "tol": TOL,
            "source": why,
        }
    )
    return diff, var


got = add(
    "unit",
    [1.0, 3.0],
    [0.0, 2.0],
    "means 2 and 1, squares 1+1+1+1 over 2: s = sqrt 2, d = 1/sqrt 2",
)
assert got == (1, 2)
got = add(
    "two", [4.0, 6.0, 8.0], [0.0, 2.0, 4.0], "means 6 and 2, squares 8 + 8 over 4: s = 2, d = 2"
)
assert got == (4, 4)
got = add("negative", [0.0, 2.0, 4.0], [4.0, 6.0, 8.0], "the same, swapped: d = -2")
assert got == (-4, 4)
got = add("equal_means", [1.0, 2.0, 3.0], [0.0, 2.0, 4.0], "means 2 and 2: d = 0")
assert got[0] == 0
rng = random.Random(397)
x = [rng.gauss(10.5, 2.0) for _ in range(40)]
y = [rng.gauss(10.0, 2.0) for _ in range(60)]
add("gaussian", x, y, "40 and 60 values from random.Random(397), N(10.5, 2) and N(10, 2)")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cohen_d.{cid}",
            "op": "cohen_d",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_too_short", "each sample needs 2 values", x=[1.0])
err("y_empty", "each sample needs 2 values", y=[])
err("not_finite", "values must be finite", x=[1.0, "nan", 3.0])
err("no_spread", "s = 0: every value at its mean", x=[2.0, 2.0], y=[5.0, 5.0, 5.0])

doc = {
    "schema": 1,
    "suite": "cohen_d",
    "description": "Cohen's d (conventions: Cohen's d; ADR 0397).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cohen_d.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cohen_d.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
