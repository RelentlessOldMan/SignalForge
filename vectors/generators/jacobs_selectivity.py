"""Writes vectors/cases/jacobs_selectivity.json, stdlib only.

Jacobs' selectivity index (conventions: Jacobs' selectivity index; ADR 0604): the shares
of each record and (p - r)/(p + r - 2pr) for each kind with fractions, 0 where p = r.

Run from the repo root: python vectors/generators/jacobs_selectivity.py [--check]
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


def add(cid, x, available, why):
    xs = [Fr(a) for a in x]
    avs = [Fr(c) for c in available]
    sx = sum(xs)
    sa = sum(avs)
    f = []
    for a, c in zip(xs, avs):
        p = a / sx
        q = c / sa
        f.append(Fr(0) if p == q else (p - q) / (p + q - 2 * p * q))
    v = [D(fi.numerator) / D(fi.denominator) for fi in f]
    cases.append(
        {
            "id": f"jacobs_selectivity.{cid}",
            "op": "jacobs_selectivity",
            "args": {"x": x, "available": available},
            "expected": [float(vi) + 0.0 for vi in v],
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add(
    "as_available", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "use as availability: 0 for each kind"
) == [0, 0, 0]
assert add("even_use", [1.0, 1.0], [1.0, 3.0], "halves on 1/4, 3/4: (1/4)/(1/2), (-1/4)/(1/2)") == [
    Fr(1, 2),
    Fr(-1, 2),
]
assert add(
    "one_kind_used", [1.0, 0.0], [1.0, 3.0], "1, 0 on 1/4, 3/4: (3/4)/(3/4), (-3/4)/(3/4)"
) == [1, -1]
assert add(
    "uneven", [2.0, 1.0, 1.0], [1.0, 2.0, 1.0], "1/2, 1/4, 1/4 on 1/4, 1/2, 1/4: 1/2, -1/2, 0"
) == [Fr(1, 2), Fr(-1, 2), 0]
assert add("one_kind", [2.0], [5.0], "one kind, p = r = 1: 0 by definition") == [0]
assert add(
    "huge", [1e308, 1e308], [1.0, 3.0], "the sum of x would overflow: halves on 1/4, 3/4: 1/2, -1/2"
) == [Fr(1, 2), Fr(-1, 2)]
f = add(
    "tiny",
    [5e-324, 1.0],
    [1.0, 1.0],
    "the smallest double counts: -1 + 4e-323 and 1 - 4e-323, -1 and 1 to double precision",
)
assert abs(f[0] + 1) < Fr(1, 10**320) and abs(f[1] - 1) < Fr(1, 10**320)
rng = random.Random(604)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
x[0] = 1.0
available = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    available,
    "x then available, 25 values each from random.Random(604)"
    ".choice([0, 0, 1, 2.5]) with x[0] = 1, and .choice([0.5, 1, 2.5])",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "available": [1.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"jacobs_selectivity.{cid}",
            "op": "jacobs_selectivity",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], available=[])
err("negative", "values must be at least 0", x=[1.0, -0.5, 2.0])
err("all_zero", "a record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", available=[1.0, 2.0])
err("unavailable", "available must be above 0 everywhere", available=[1.0, 0.0, 1.0])
err("underflow", "the share 5e-324/1e300 underflows to 0", available=[1e300, 5e-324, 1.0])

doc = {
    "schema": 1,
    "suite": "jacobs_selectivity",
    "description": "Jacobs' selectivity index (conventions: Jacobs' selectivity index; ADR 0604).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "jacobs_selectivity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/jacobs_selectivity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
