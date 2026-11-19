"""Writes vectors/cases/cramer_von_mises.json, stdlib only.

The two-sample Cramer-von Mises statistic (conventions: two-sample Cramer-von Mises statistic;
ADR 0405): both empirical distribution functions at every pooled value, exact in rationals.

Run from the repo root: python vectors/generators/cramer_von_mises.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def add(cid, x, y, why):
    nx, ny = len(x), len(y)
    total = sum(
        (Fr(sum(v <= z for v in x), nx) - Fr(sum(v <= z for v in y), ny)) ** 2 for z in x + y
    )
    t = Fr(nx * ny, (nx + ny) ** 2) * total
    cases.append(
        {
            "id": f"cramer_von_mises.{cid}",
            "op": "cramer_von_mises",
            "args": {"x": x, "y": y},
            "expected": float(t),
            "tol": TOL,
            "source": why,
        }
    )
    return t


got = add("one_each", [1.0], [4.0], "z = 1: (1 - 0)^2; z = 4: 0. 1/4 * 1 = 1/4")
assert got == Fr(1, 4)
got = add("same", [3.0, 1.0, 2.0], [2.0, 3.0, 1.0], "the same values: 0")
assert got == 0
got = add(
    "hand",
    [1.0, 2.0, 3.0],
    [2.0, 4.0],
    "squared gaps 1/9 at 1, 1/36 twice at 2, 1/4 at 3, 0 at 4: sum 5/12, times 6/25 = 1/10",
)
assert got == Fr(1, 10)
got = add(
    "apart",
    [1.0, 2.0],
    [5.0, 6.0],
    "squared gaps 1/4, 1, 1/4, 0 at 1, 2, 5, 6: sum 3/2, times 4/16 = 3/8",
)
assert got == Fr(3, 8)
rng = random.Random(405)
x = [round(rng.gauss(0.3, 1.0), 1) for _ in range(40)]
y = [round(rng.gauss(0.0, 2.0), 1) for _ in range(55)]
add(
    "rounded_gaussian",
    x,
    y,
    "40 and 55 values from random.Random(405), N(0.3, 1) and N(0, 2) rounded to 0.1, so with ties",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cramer_von_mises.{cid}",
            "op": "cramer_von_mises",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_empty", "y needs a value", y=[])
err("not_finite", "values must be finite", x=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "cramer_von_mises",
    "description": "The two-sample Cramer-von Mises statistic (conventions: two-sample "
    "Cramer-von Mises statistic; ADR 0405).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cramer_von_mises.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cramer_von_mises.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
