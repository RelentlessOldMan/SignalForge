"""Writes vectors/cases/cliff_delta.json, stdlib only.

Cliff's delta (conventions: Cliff's delta; ADR 0400): every pair compared, the share exact in
rationals.

Run from the repo root: python vectors/generators/cliff_delta.py [--check]
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
    net = sum((a > b) - (a < b) for a in x for b in y)
    delta = Fr(net, len(x) * len(y))
    cases.append(
        {
            "id": f"cliff_delta.{cid}",
            "op": "cliff_delta",
            "args": {"x": x, "y": y},
            "expected": float(delta),
            "tol": TOL,
            "source": why,
        }
    )
    return delta


got = add("above", [5.0, 6.0], [1.0, 2.0, 3.0], "every x above every y: 1")
assert got == 1
got = add("below", [1.0, 2.0], [5.0, 6.0, 7.0], "every x below every y: -1")
assert got == -1
got = add("all_tied", [2.0, 2.0], [2.0, 2.0, 2.0], "every pair tied: 0")
assert got == 0
got = add(
    "hand",
    [1.0, 3.0, 5.0],
    [2.0, 3.0, 4.0],
    "x = 1 loses 3; 3 beats 2, ties 3, loses to 4; 5 beats 3: (4 - 4)/9 = 0",
)
assert got == 0
got = add(
    "hand_two",
    [2.0, 4.0, 6.0, 8.0],
    [1.0, 5.0],
    "wins 1 + 1 + 2 + 2 = 6, losses 1 + 1 = 2: 4/8 = 1/2",
)
assert got == Fr(1, 2)
rng = random.Random(400)
x = [round(rng.gauss(10.5, 2.0)) for _ in range(40)]
y = [round(rng.gauss(10.0, 2.0)) for _ in range(55)]
add(
    "rounded_gaussian",
    x,
    y,
    "40 and 55 values from random.Random(400), N(10.5, 2) and "
    "N(10, 2) rounded to integers, so with ties",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cliff_delta.{cid}",
            "op": "cliff_delta",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_empty", "y needs a value", y=[])
err("not_finite", "values must be finite", y=[2.0, "nan"])

doc = {
    "schema": 1,
    "suite": "cliff_delta",
    "description": "Cliff's delta (conventions: Cliff's delta; ADR 0400).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cliff_delta.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cliff_delta.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
