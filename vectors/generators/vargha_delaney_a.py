"""Writes vectors/cases/vargha_delaney_a.json, stdlib only.

The Vargha-Delaney A (conventions: Vargha-Delaney A; ADR 0401): every pair compared, a win 2
and a tie 1, exact in rationals.

Run from the repo root: python vectors/generators/vargha_delaney_a.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, x, y, why):
    score = sum(2 if a > b else 1 if a == b else 0 for a in x for b in y)
    va = Fr(score, 2 * len(x) * len(y))
    cases.append(
        {
            "id": f"vargha_delaney_a.{cid}",
            "op": "vargha_delaney_a",
            "args": {"x": x, "y": y},
            "expected": float(va),
            "tol": TOL,
            "source": why,
        }
    )
    return va


got = add("above", [5.0, 6.0], [1.0, 2.0, 3.0], "every x above every y: 1")
assert got == 1
got = add("below", [1.0, 2.0], [5.0, 6.0, 7.0], "every x below every y: 0")
assert got == 0
got = add("all_tied", [2.0, 2.0], [2.0, 2.0, 2.0], "every pair tied: 1/2")
assert got == Fr(1, 2)
got = add("hand", [1.0, 3.0, 5.0], [2.0, 3.0, 4.0], "wins 4, ties 1 (3 = 3): (8 + 1)/18 = 1/2")
assert got == Fr(1, 2)
got = add(
    "hand_two",
    [2.0, 4.0, 6.0, 8.0],
    [1.0, 5.0, 6.0],
    "wins 1 + 1 + 2 + 3 = 7, ties 1 (6 = 6): (14 + 1)/24 = 5/8",
)
assert got == Fr(5, 8)
rng = random.Random(401)
x = [round(rng.gauss(10.5, 2.0)) for _ in range(40)]
y = [round(rng.gauss(10.0, 2.0)) for _ in range(55)]
add(
    "rounded_gaussian",
    x,
    y,
    "40 and 55 values from random.Random(401), N(10.5, 2) and "
    "N(10, 2) rounded to integers, so with ties",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"vargha_delaney_a.{cid}",
            "op": "vargha_delaney_a",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_empty", "y needs a value", y=[])
err("not_finite", "values must be finite", x=["inf", 2.0])

doc = {
    "schema": 1,
    "suite": "vargha_delaney_a",
    "description": "The Vargha-Delaney A (conventions: Vargha-Delaney A; ADR 0401).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "vargha_delaney_a.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/vargha_delaney_a.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
