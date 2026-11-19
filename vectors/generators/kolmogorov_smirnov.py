"""Writes vectors/cases/kolmogorov_smirnov.json, stdlib only.

The two-sample Kolmogorov-Smirnov statistic (conventions: two-sample Kolmogorov-Smirnov
statistic; ADR 0402): both empirical distribution functions at every pooled value, exact in
rationals.

Run from the repo root: python vectors/generators/kolmogorov_smirnov.py [--check]
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
    d = max(
        abs(Fr(sum(v <= t for v in x), len(x)) - Fr(sum(v <= t for v in y), len(y))) for t in x + y
    )
    cases.append(
        {
            "id": f"kolmogorov_smirnov.{cid}",
            "op": "kolmogorov_smirnov",
            "args": {"x": x, "y": y},
            "expected": float(d),
            "tol": TOL,
            "source": why,
        }
    )
    return d


got = add("apart", [1.0, 2.0], [5.0, 6.0, 7.0], "no overlap: 1")
assert got == 1
got = add("same", [3.0, 1.0, 2.0], [2.0, 3.0, 1.0], "the same values: 0")
assert got == 0
got = add(
    "hand",
    [1.0, 2.0, 3.0],
    [2.0, 4.0],
    "at t = 1: 1/3 - 0; t = 2: 2/3 - 1/2; t = 3: 1 - 1/2 = 1/2; t = 4: 0. Max 1/2",
)
assert got == Fr(1, 2)
got = add(
    "spread",
    [0.0, 0.0, 0.0, 0.0],
    [-1.0, 0.0, 1.0],
    "same median; t = -1: 0 - 1/3; t = 0: 1 - 2/3; t = 1: 0. Max 1/3",
)
assert got == Fr(1, 3)
rng = random.Random(402)
x = [round(rng.gauss(0.3, 1.0), 1) for _ in range(40)]
y = [round(rng.gauss(0.0, 1.0), 1) for _ in range(55)]
add(
    "rounded_gaussian",
    x,
    y,
    "40 and 55 values from random.Random(402), N(0.3, 1) and N(0, 1) rounded to 0.1, so with ties",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"kolmogorov_smirnov.{cid}",
            "op": "kolmogorov_smirnov",
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
    "suite": "kolmogorov_smirnov",
    "description": "The two-sample Kolmogorov-Smirnov statistic (conventions: two-sample "
    "Kolmogorov-Smirnov statistic; ADR 0402).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kolmogorov_smirnov.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kolmogorov_smirnov.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
